#!/usr/bin/env node
// Static analyzer for Vue 3 SFCs. Emits JSON facts (not judgments) that the
// skill then interprets. Usage:
//   node analyze.mjs --root <client-dir> [files-or-dirs...]
// --root is where node_modules/@vue/compiler-sfc lives; paths default to <root>/src.

import { createRequire } from "node:module";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { createHash } from "node:crypto";

const args = process.argv.slice(2);
let root = process.cwd();
const targets = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--root") root = resolve(args[++i]);
  else targets.push(resolve(args[i]));
}
if (!targets.length) targets.push(join(root, "src"));

let sfc, dom;
try {
  const req = createRequire(join(root, "package.json"));
  sfc = req("@vue/compiler-sfc");
  dom = req("@vue/compiler-dom");
} catch {
  console.error(
    `Cannot load @vue/compiler-sfc from ${root}. Run npm install there or pass --root <dir with node_modules>.`,
  );
  process.exit(1);
}
const { NodeTypes } = dom;

function collect(p, out = []) {
  const st = statSync(p);
  if (st.isDirectory()) {
    for (const f of readdirSync(p)) {
      if (f === "node_modules" || f.startsWith(".")) continue;
      collect(join(p, f), out);
    }
  } else if (p.endsWith(".vue")) out.push(p);
  return out;
}
const files = [...new Set(targets.flatMap((t) => collect(t)))].sort();

const hash = (s) => createHash("sha1").update(s).digest("hex").slice(0, 10);
// Strip whitespace and comments so cosmetic differences don't hide duplicates
const normalize = (s) =>
  s
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\/\/.*$/gm, "")
    .replace(/\s+/g, "");

const report = {
  root: relative(process.cwd(), root) || ".",
  files: [],
  crossFile: {},
};
const fnIndex = new Map(); // normalized body hash -> [{file, name, line}]
const fnNameIndex = new Map(); // function name -> [{file, line}]
const cssIndex = new Map(); // selector -> [{file, declHash}]
const subtreeIndex = new Map(); // template subtree hash -> [{file, line, tag}]

for (const abs of files) {
  const rel = relative(process.cwd(), abs);
  const src = readFileSync(abs, "utf8");
  const { descriptor, errors } = sfc.parse(src, { filename: abs });
  const f = {
    file: rel,
    lines: src.split("\n").length,
    blocks: {
      template: descriptor.template
        ? descriptor.template.content.split("\n").length
        : 0,
      script:
        (descriptor.scriptSetup || descriptor.script)?.content.split("\n")
          .length || 0,
      style: descriptor.styles.reduce(
        (n, s) => n + s.content.split("\n").length,
        0,
      ),
    },
    scriptStyle: descriptor.scriptSetup
      ? "script-setup"
      : descriptor.script
        ? "options-or-setup()"
        : "none",
    styleScoped: descriptor.styles.map((s) => !!s.scoped),
    parseErrors: errors.map((e) => String(e.message || e)),
    template: {},
    script: {},
    findings: [],
  };
  const add = (rule, line, detail) => f.findings.push({ rule, line, detail });

  // ---------- template ----------
  if (descriptor.template?.ast) {
    const t = {
      elements: 0,
      maxDepth: 0,
      vFor: 0,
      vIf: 0,
      vShow: 0,
      components: new Set(),
      inlineSvg: 0,
      interpolationCalls: 0,
    };
    const tplLineOffset = 0; // AST locs are already file-relative
    const walk = (node, depth, inFor) => {
      if (node.type === NodeTypes.ELEMENT) {
        t.elements++;
        t.maxDepth = Math.max(t.maxDepth, depth);
        if (node.tagType === 1) t.components.add(node.tag);
        if (node.tag === "svg") t.inlineSvg++;
        const line = node.loc.start.line + tplLineOffset;
        const dirs = node.props.filter((p) => p.type === NodeTypes.DIRECTIVE);
        const vfor = dirs.find((d) => d.name === "for");
        const vif = dirs.find((d) => d.name === "if");
        if (vif) t.vIf++;
        if (dirs.some((d) => d.name === "show")) t.vShow++;
        if (vfor) {
          t.vFor++;
          const keyProp = node.props.find(
            (p) =>
              (p.type === NodeTypes.DIRECTIVE &&
                p.name === "bind" &&
                p.arg?.content === "key") ||
              (p.type === NodeTypes.ATTRIBUTE && p.name === "key"),
          );
          const forSrc = vfor.exp?.loc.source || "";
          const alias = forSrc.match(/^\(?\s*\w+\s*,\s*(\w+)/)?.[1];
          if (!keyProp) add("vfor-missing-key", line, forSrc);
          else if (keyProp.exp && alias && keyProp.exp.content.trim() === alias)
            add("vfor-index-key", line, `${forSrc} :key="${alias}"`);
          if (vif)
            add(
              "vfor-with-vif",
              line,
              `v-for="${forSrc}" v-if="${vif.exp?.loc.source}"`,
            );
          // Function calls in the iterable are re-run on every render
          if (/\w\s*\(/.test(forSrc.split(/\s+(?:in|of)\s+/)[1] || ""))
            add("vfor-calls-function", line, forSrc);
        }
        for (const d of dirs) {
          if (
            d.name === "on" &&
            inFor &&
            d.exp &&
            /=>|\bfunction\b/.test(d.exp.content)
          )
            add(
              "inline-handler-in-loop",
              d.loc.start.line,
              `@${d.arg?.content}="${d.exp.content}"`,
            );
          // Fresh object/array literals only defeat memoization when passed as props to a child component;
          // on plain elements (:class/:style) Vue diffs them cheaply, so skip those
          if (
            d.name === "bind" &&
            inFor &&
            node.tagType === 1 &&
            d.exp &&
            /^\s*[{[]/.test(d.exp.content) &&
            d.arg?.content !== "key"
          )
            add(
              "object-literal-prop-in-loop",
              d.loc.start.line,
              `:${d.arg?.content}="${d.exp.content.slice(0, 60)}"`,
            );
        }
        // Record sizeable subtrees for cross-file duplicate detection
        const s = node.loc.source;
        if (s.length > 400 && node.children.length >= 3) {
          const h = hash(
            normalize(
              s.replace(/\{\{[^}]*\}\}/g, "{{}}").replace(/"[^"]*"/g, '""'),
            ),
          );
          if (!subtreeIndex.has(h)) subtreeIndex.set(h, []);
          subtreeIndex
            .get(h)
            .push({ file: rel, line, tag: node.tag, chars: s.length });
        }
        for (const c of node.children) walk(c, depth + 1, inFor || !!vfor);
      } else if (node.type === NodeTypes.INTERPOLATION) {
        const e = node.content.loc.source;
        if (/\w\s*\(/.test(e)) {
          t.interpolationCalls++;
          // Heavy array ops inside the template run on every re-render
          if (/\.(filter|map|reduce|sort|find|slice)\s*\(/.test(e))
            add(
              "array-op-in-template",
              node.loc.start.line,
              e.trim().slice(0, 80),
            );
        }
      } else if (node.children) {
        for (const c of node.children) walk(c, depth, inFor);
      }
      if (node.branches) for (const b of node.branches) walk(b, depth, inFor);
    };
    walk(descriptor.template.ast, 0, false);
    t.components = [...t.components];
    f.template = t;
  }

  // ---------- script ----------
  const block = descriptor.scriptSetup || descriptor.script;
  if (block) {
    const code = block.content;
    const base = block.loc.start.line - 1;
    const lineOf = (idx) => base + code.slice(0, idx).split("\n").length;
    const count = (re) => (code.match(re) || []).length;
    const s = {
      imports: [...code.matchAll(/^import\s+.*?from\s+['"]([^'"]+)['"]/gm)].map(
        (m) => m[1],
      ),
      ref: count(/\bref\s*\(/g),
      reactive: count(/\breactive\s*\(/g),
      computed: count(/\bcomputed\s*\(/g),
      watch: count(/\bwatch\s*\(/g),
      watchEffect: count(/\bwatchEffect\s*\(/g),
      onMounted: count(/\bonMounted\s*\(/g),
      apiCalls: count(/\bapi\.\w+\s*\(/g),
      tryCatch: count(/\btry\s*\{/g),
    };
    f.script = s;

    for (const m of code.matchAll(/deep\s*:\s*true/g))
      add("deep-watch", lineOf(m.index), "watch(..., { deep: true })");
    for (const m of code.matchAll(/JSON\.parse\s*\(\s*JSON\.stringify/g))
      add(
        "json-deep-clone",
        lineOf(m.index),
        "JSON.parse(JSON.stringify(...))",
      );
    for (const m of code.matchAll(/\b(?:ref|reactive)\s*\(\s*\[\s*\]\s*\)/g)) {
      // Large arrays held in deep ref; shallowRef avoids proxying every element
      add("deep-ref-array", lineOf(m.index), m[0]);
    }
    if (/setInterval\s*\(/.test(code) && !/clearInterval/.test(code))
      add(
        "interval-not-cleared",
        lineOf(code.indexOf("setInterval")),
        "setInterval without clearInterval",
      );
    if (/addEventListener\s*\(/.test(code) && !/removeEventListener/.test(code))
      add(
        "listener-not-removed",
        lineOf(code.indexOf("addEventListener")),
        "addEventListener without removeEventListener",
      );
    if (
      /\bloading\s*=\s*ref\(/.test(code) &&
      /\berror\s*=\s*ref\(/.test(code) &&
      s.apiCalls
    )
      add(
        "loading-error-fetch-pattern",
        lineOf(code.search(/\bloading\s*=\s*ref\(/)),
        "loading/error refs + api call (composable candidate)",
      );

    // Named function definitions: const x = (...) => {...} / function x(...) {...}
    const fnRe =
      /(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*|function\s+(\w+)\s*\([^)]*\)\s*/g;
    for (const m of code.matchAll(fnRe)) {
      const name = m[1] || m[2];
      // Grab the body by brace matching (or single expression for arrow fns)
      let i = m.index + m[0].length,
        body;
      if (code[i] === "{") {
        let d = 0,
          j = i;
        for (; j < code.length; j++) {
          if (code[j] === "{") d++;
          else if (code[j] === "}" && --d === 0) break;
        }
        body = code.slice(i, j + 1);
      } else body = code.slice(i, code.indexOf("\n", i));
      const entry = {
        file: rel,
        name,
        line: lineOf(m.index),
        bodyLines: body.split("\n").length,
      };
      if (!fnNameIndex.has(name)) fnNameIndex.set(name, []);
      fnNameIndex.get(name).push(entry);
      const n = normalize(body);
      if (n.length > 40) {
        const h = hash(n);
        if (!fnIndex.has(h)) fnIndex.set(h, []);
        fnIndex.get(h).push(entry);
      }
    }
  }

  // ---------- styles ----------
  for (const st of descriptor.styles) {
    const css = st.content.replace(/\/\*[\s\S]*?\*\//g, "");
    for (const m of css.matchAll(/([^{}@]+)\{([^{}]*)\}/g)) {
      const decl = normalize(m[2]);
      if (!decl) continue;
      for (const sel of m[1]
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean)) {
        if (!cssIndex.has(sel)) cssIndex.set(sel, []);
        cssIndex.get(sel).push({ file: rel, declHash: hash(decl) });
      }
    }
  }

  report.files.push(f);
}

// ---------- cross-file ----------
const multiFile = (list) => new Set(list.map((e) => e.file)).size > 1;
report.crossFile.duplicateFunctionBodies = [...fnIndex.values()].filter(
  multiFile,
);
report.crossFile.sameNameFunctions = [...fnNameIndex.entries()]
  .filter(([, l]) => multiFile(l))
  .map(([name, l]) => ({
    name,
    sites: l.map(({ file, line }) => ({ file, line })),
  }));
report.crossFile.duplicateTemplateSubtrees = [...subtreeIndex.values()].filter(
  (l) => l.length > 1,
);
report.crossFile.sharedCssSelectors = [...cssIndex.entries()]
  .filter(([, l]) => multiFile(l))
  .map(([selector, l]) => ({
    selector,
    files: [...new Set(l.map((e) => e.file))],
    identicalDeclarations: new Set(l.map((e) => e.declHash)).size === 1,
  }))
  .sort((a, b) => b.files.length - a.files.length);
report.summary = {
  files: report.files.length,
  largest: [...report.files]
    .sort((a, b) => b.lines - a.lines)
    .slice(0, 5)
    .map((f) => `${f.file} (${f.lines})`),
  findingsByRule: report.files
    .flatMap((f) => f.findings)
    .reduce((a, x) => ((a[x.rule] = (a[x.rule] || 0) + 1), a), {}),
};

console.log(JSON.stringify(report, null, 2));
