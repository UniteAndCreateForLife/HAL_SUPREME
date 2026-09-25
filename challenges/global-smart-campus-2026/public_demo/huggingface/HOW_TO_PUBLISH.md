# Publishing the demo as a Hugging Face Space

The Space is static: no server, no GPU, no paid hardware.

1. On huggingface.co, create a new Space named `hal-campus-evidence-desk`, SDK **Static**, visibility **Public**.
2. Upload three files to the Space root:
   - `huggingface/README.md` (the Space card, uploaded as `README.md`)
   - `public/index.html`
   - `public/gate.js`
3. Open the Space and run each draft once to confirm the gate renders.

With the Hugging Face CLI instead (after `huggingface-cli login` with your own token):

```bash
huggingface-cli upload <your-username>/hal-campus-evidence-desk huggingface/README.md README.md --repo-type space
huggingface-cli upload <your-username>/hal-campus-evidence-desk public/index.html index.html --repo-type space
huggingface-cli upload <your-username>/hal-campus-evidence-desk public/gate.js gate.js --repo-type space
```

Upload the files from the same commit as the GitHub source so the Space matches the tested code.
