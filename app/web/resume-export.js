export function resumeText({name, contact, blocks, additions}) {
  const parts = [name.trim(), contact.trim()];
  for (const block of blocks) if (block.text.trim()) parts.push(block.title + "\n" + block.text.trim());
  if (additions.trim()) parts.push("Informações complementares\n" + additions.trim());
  return parts.filter(Boolean).join("\n\n") + "\n";
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

export function resumeHtml({name, contact, blocks, additions}) {
  const sections = blocks.filter(block => block.text.trim()).map(block =>
    "<section><h2>" + escapeHtml(block.title) + "</h2><p>" + escapeHtml(block.text.trim()) + "</p></section>",
  );
  if (additions.trim()) sections.push("<section><h2>Informações complementares</h2><p>" + escapeHtml(additions.trim()) + "</p></section>");
  return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">' +
    '<title>Currículo — ' + escapeHtml(name.trim()) + '</title><style>' +
    '@page{size:A4;margin:18mm}body{max-width:760px;margin:40px auto;padding:0 24px;color:#182c2d;font:11pt/1.5 Arial,sans-serif}' +
    'h1{font-size:24pt;margin-bottom:6px}h2{font-size:13pt;border-bottom:1px solid #a7b6b6;padding-bottom:4px;margin-top:24px}' +
    'p{white-space:pre-wrap;overflow-wrap:anywhere}section{break-inside:avoid}@media print{body{margin:0;padding:0;max-width:none}}' +
    '</style></head><body><header><h1>' + escapeHtml(name.trim()) + '</h1>' +
    (contact.trim() ? '<p>' + escapeHtml(contact.trim()) + '</p>' : '') +
    '</header><main>' + sections.join('') + '</main></body></html>';
}
