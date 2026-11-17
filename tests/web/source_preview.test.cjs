// Run with: node --test tests/web/source_preview.test.cjs
// The VM supplies fake devices, timers, and API responses; no audio is opened.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../../src/local_meeting_ai/web/static/js/transcript.js"), "utf8");
function extract(start, end) {
  const first = source.indexOf(start);
  const last = source.indexOf(end, first + start.length);
  assert.ok(first >= 0 && last > first, `Could not find source section: ${start}`);
  return source.slice(first, last);
}

function setup() {
  const timers = new Map();
  const requests = [];
  let timerId = 0;
  let previewHandler;
  let resolveProbe;
  const classes = {add() {}, remove() {}, toggle() {}};
  const button = {
    attrs: {}, textContent: "", disabled: false,
    setAttribute(key, value) { this.attrs[key] = value; },
    addEventListener(_name, handler) { previewHandler = handler; },
  };
  const bar = {style: {width: "0%"}};
  const meter = {
    isConnected: true, dataset: {sourceMeter: "synthetic-mic"}, classList: classes,
    querySelector() { return bar; },
  };
  const input = {value: "synthetic-mic", checked: true, isConnected: true};
  const elements = new Map();
  function element(selector) {
    if (selector === "#preview-source-levels") return button;
    if (selector.startsWith("[data-source-meter=")) return meter;
    if (!elements.has(selector)) elements.set(selector, {classList: classes, dataset: {}, reset() {}});
    return elements.get(selector);
  }
  const dialog = {
    open: false,
    showModal() { this.open = true; },
    addEventListener(name, handler) { if (name === "close") this.onclose = handler; },
    close() { this.open = false; this.onclose(); },
  };
  const context = vm.createContext({
    document: {querySelector: element, querySelectorAll() { return [meter]; }},
    window: {
      setTimeout(fn) { const id = ++timerId; timers.set(id, fn); return id; },
      clearTimeout(id) { timers.delete(id); },
    },
    CSS: {escape: (value) => value},
    startDialog: dialog,
    selectedSourceMode: () => "microphone",
    selectedLiveModes: () => ["microphone"],
    selectedNativeSources: () => [input],
    rememberSelectedDevices() {}, syncCaptureSelection() {}, resetFilePicker() {},
    audioSources: [{id: "synthetic-mic", name: "Synthetic", kind: "microphone", is_default: true}],
    captureCapability: {available: true}, selectedDevices: {microphone: null},
    t: (key) => key, escapeHTML: (value) => value,
    api(url, options) { requests.push({url, method: options.method, preview: options.headers["X-Meet2Notes-Preview"]}); return new Promise((resolve) => { resolveProbe = resolve; }); },
  });
  const code = [
    "let sourcePreviewTimer = null; let sourcePreviewBusy = false; let sourcePreviewEnabled = false; let sourcePreviewGeneration = 0;",
    extract("  function renderSourceMode()", "  function selectedSourceMode()"),
    extract("  function stopSourcePreview()", "  async function selectTranscription("),
    "function renderSources() { renderSourceMode(); }",
    extract("  function openStartDialog()", "  async function submitTranscription("),
    extract('  document.querySelector("#preview-source-levels").addEventListener', '  document.querySelectorAll(\'input[name="source-mode"]\')'),
    extract('  startDialog.addEventListener("close", stopSourcePreview);', '  document.querySelector("#transcription-form").addEventListener'),
  ].join("\n");
  vm.runInContext(code, context);
  return {
    context, dialog, button, bar, timers, requests,
    clickPreview() { previewHandler({currentTarget: button}); },
    runTimer() {
      const [id, fn] = timers.entries().next().value;
      timers.delete(id);
      return fn();
    },
    resolveProbe(value) { resolveProbe(value); },
  };
}

test("opening the dialog and rendering its sources do not probe audio", () => {
  const env = setup();
  vm.runInContext("openStartDialog()", env.context);
  assert.equal(env.dialog.open, true);
  assert.equal(env.timers.size, 0);
  assert.deepEqual(env.requests, []);
  assert.equal(env.button.attrs["aria-pressed"], "false");
});

test("explicit preview probes only the mocked device and stop ignores a late response", async () => {
  const env = setup();
  vm.runInContext("openStartDialog()", env.context);
  env.clickPreview();
  assert.equal(env.button.attrs["aria-pressed"], "true");
  const inFlight = env.runTimer();
  assert.deepEqual(env.requests, [{url: "/api/audio/sources/synthetic-mic/level", method: "POST", preview: "1"}]);
  env.clickPreview();
  assert.equal(env.button.attrs["aria-pressed"], "false");
  env.resolveProbe({level: 0.9});
  await inFlight;
  assert.equal(env.bar.style.width, "0%");
  assert.equal(env.timers.size, 0);
  vm.runInContext("scheduleSourcePreview(0)", env.context);
  assert.equal(env.timers.size, 0);
});

test("closing the dialog while a probe is pending stops future probes", async () => {
  const env = setup();
  vm.runInContext("openStartDialog()", env.context);
  env.clickPreview();
  const inFlight = env.runTimer();
  env.dialog.close();
  env.resolveProbe({level: 1});
  await inFlight;
  assert.equal(env.bar.style.width, "0%");
  assert.equal(env.timers.size, 0);
  vm.runInContext("openStartDialog()", env.context);
  assert.equal(env.timers.size, 0);
  assert.equal(env.requests.length, 1);
});
