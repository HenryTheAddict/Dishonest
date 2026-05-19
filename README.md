# Dishonesty

Real browser AI for Chrome and Chromebooks.

## Use

1. Unzip `dishonesty-real-models.zip`.
2. Open `index.html` in Chrome.
3. Pick a model in Model Hub.

All listed models are real ONNX language models for Transformers.js/WebGPU:

- Qwen 2.5 0.5B
- Qwen 2.5 Coder 0.5B
- Gemma 3 1B IT

Each model needs internet the first time Chrome downloads it. After that, Chrome may reuse the browser cache on the same device.

## Runtime Controls

The Settings page includes temperature, max tokens, top-p, repeat penalty, sampling, device, quantization, and system prompt controls. Settings save in the browser automatically.

## Local Tools

Use `/math 2 + 2`, `/ascii hello`, or `/preview <h1>Hello</h1>` in chat. Model responses render Markdown, including code blocks and lists, and HTML previews open in a sandboxed iframe.

## Release Packs

GitHub Actions builds release assets:

- `dishonesty-app.zip`: app only
- `dishonesty-model-pack-small.zip`: Qwen 2.5 0.5B
- `dishonesty-model-pack-good.zip`: Gemma 3 1B IT + Qwen Coder 0.5B
- `dishonesty-model-pack-all.zip`: every listed model
- `models.zip`: single-file megapack with every listed q4 model, uploaded as the `dishonesty-model-megapack` workflow artifact because it is too large for GitHub Release assets

Model packs are stored ZIPs that can be imported from Model Hub with **Import Release Pack**. The importer writes files into the browser `transformers-cache`, then the app detects cached models automatically.

If the app is served from a local folder or static host, it also tries to auto-import known same-folder pack names such as `models.zip`, `dishonesty-model-pack-small.zip`, and split release parts like `dishonesty-model-pack-all-part-01.zip`. Browsers do not allow this kind of automatic folder access from plain `file://`, so use **Import Release Pack** there.
