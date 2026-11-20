/**
 * ClaudeSheets – Gọi Claude (Anthropic API) ngay trong Google Sheets.
 *
 *   =CLAUDE("Tóm tắt nội dung"; A2:D20)
 *   Menu "🤖 Claude" → Cài API key / Hỏi Claude về vùng chọn / Xử lý từng ô
 *
 * Xem HUONG_DAN.md để cài đặt.
 */

// ----------------------------- CẤU HÌNH -----------------------------------
const API_URL = 'https://api.anthropic.com/v1/messages';
const API_VERSION = '2026-10-21';
// Model mặc định. Muốn nhanh/rẻ hơn: 'claude-sonnet-5-5' hoặc 'claude-haiku-5-5'.
const MODEL_MAC_DINH = 'claude-opus-5-5';
const MAX_TOKENS = 16000;
// Mức "suy nghĩ": low | medium | high | xhigh | max. "low" cho trả lời nhanh
// trong ô (hàm trong ô của Google Sheets bị giới hạn 30 giây).
const EFFORT = 'low';
const GIOI_HAN_O = 50000;              // giới hạn ký tự của 1 ô Google Sheets
const SO_O_CHAY_SONG_SONG = 8;         // macro "Xử lý từng ô" gửi mỗi đợt 8 yêu cầu
const THOI_GIAN_TOI_DA_MS = 5 * 60 * 1000; // script bị Google dừng ở 6 phút

const SYSTEM_O =
  'Bạn là trợ lý chạy bên trong một ô bảng tính. Chỉ trả về kết quả cuối cùng, ' +
  'ngắn gọn, không giải thích, không chào hỏi, không dùng markdown. ' +
  'Trả lời bằng ngôn ngữ của yêu cầu.';

const SYSTEM_BANG =
  'Bạn là trợ lý phân tích dữ liệu cho người dùng Google Sheets. Không dùng markdown ' +
  '(không **, không #, không ```). Nếu câu trả lời có dạng bảng, hãy trả về bảng dạng ' +
  'TSV: mỗi dòng một hàng, các cột cách nhau bằng ký tự TAB, dòng đầu là tiêu đề. ' +
  'Số liệu viết dạng số thuần (vd 1234567.5), không dấu phân cách hàng nghìn, không ' +
  'kèm đơn vị trong ô số. Trả lời bằng ngôn ngữ của câu hỏi.';

// --------------------------------------------------------------------------
//                         HÀM DÙNG TRONG Ô
// --------------------------------------------------------------------------

/**
 * Hỏi Claude ngay trong ô.
 *
 * @param {string} yeu_cau Câu lệnh / câu hỏi.
 * @param {A1:D20} du_lieu (Tùy chọn) Vùng ô hoặc giá trị gửi kèm.
 * @param {string} model (Tùy chọn) vd "claude-haiku-5-5".
 * @return Câu trả lời của Claude.
 * @customfunction
 */
function CLAUDE(yeu_cau, du_lieu, model) {
  try {
    let prompt = giaTriThanhChu(yeu_cau).trim();
    if (!prompt) return '';
    if (du_lieu !== undefined && du_lieu !== null && du_lieu !== '') {
      const d = giaTriThanhChu(du_lieu);
      if (d) prompt += '\n\n<du_lieu>\n' + d + '\n</du_lieu>';
    }
    model = model || MODEL_MAC_DINH;

    // Bộ nhớ đệm 6 giờ: cùng yêu cầu + dữ liệu thì không gọi lại API.
    const cache = CacheService.getScriptCache();
    const khoa = 'c_' + bam(model + '\u0000' + SYSTEM_O + '\u0000' + prompt);
    const daCo = cache.get(khoa);
    if (daCo !== null) return daCo;

    const kq = catChoVuaO(goiClaude(prompt, SYSTEM_O, model, 1));
    if (kq.length < 90000) cache.put(khoa, kq, 21600);
    return kq;
  } catch (e) {
    return '#CLAUDE: ' + e.message;
  }
}

// --------------------------------------------------------------------------
//                               MENU
// --------------------------------------------------------------------------

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🤖 Claude')
    .addItem('Hỏi Claude về vùng đang chọn…', 'hoiClaudeVeVungChon')
    .addItem('Xử lý từng ô (ghi kết quả sang cột phải)…', 'claudeXuLyTungO')
    .addSeparator()
    .addItem('Cài API key…', 'caiDatApiKey')
    .addItem('Xóa API key', 'xoaApiKey')
    .addToUi();
}

function caiDatApiKey() {
  const ui = SpreadsheetApp.getUi();
  const r = ui.prompt('Claude – API key',
    'Dán Anthropic API key (sk-ant-...).\nLấy tại platform.claude.com → API Keys.',
    ui.ButtonSet.OK_CANCEL);
  if (r.getSelectedButton() !== ui.Button.OK) return;
  const k = r.getResponseText().trim();
  if (!k) return;
  PropertiesService.getScriptProperties().setProperty('ANTHROPIC_API_KEY', k);
  ui.alert('Đã lưu API key. Thử gõ vào 1 ô:  =CLAUDE("Xin chào")');
}

function xoaApiKey() {
  PropertiesService.getScriptProperties().deleteProperty('ANTHROPIC_API_KEY');
  SpreadsheetApp.getUi().alert('Đã xóa API key.');
}

/** Hỏi Claude về vùng đang chọn; kết quả (chữ hoặc bảng) ra sheet mới. */
function hoiClaudeVeVungChon() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActive();
  const vung = ss.getActiveRange();
  const r = ui.prompt('Hỏi Claude',
    'Bạn muốn hỏi gì về vùng ' + (vung ? vung.getA1Notation() : '') + '?\n' +
    'Vd: Tổng hợp công nợ theo chủ đầu tư; Tìm dòng bất thường; Lập bảng kê…',
    ui.ButtonSet.OK_CANCEL);
  if (r.getSelectedButton() !== ui.Button.OK) return;
  const cauHoi = r.getResponseText().trim();
  if (!cauHoi) return;

  let prompt = cauHoi;
  if (vung) {
    const d = giaTriThanhChu(catVungCoDuLieu(vung).getDisplayValues());
    if (d.replace(/[\t\n]/g, '')) {
      prompt += '\n\n<du_lieu sheet="' + vung.getSheet().getName() + '" vung="' +
        vung.getA1Notation() + '">\n' + d + '\n</du_lieu>';
    }
  }

  ss.toast('Claude đang trả lời…', 'Claude', -1);
  let kq;
  try {
    kq = goiClaude(prompt, SYSTEM_BANG, MODEL_MAC_DINH, 3);
  } catch (e) {
    ss.toast('', 'Claude', 1);
    ui.alert('Lỗi: ' + e.message);
    return;
  }

  const ten = 'Claude ' + Utilities.formatDate(new Date(), ss.getSpreadsheetTimeZone(), 'ddMM HHmmss');
  const ws = ss.insertSheet(ten, ss.getNumSheets());
  ws.getRange('A1').setValue('Câu hỏi: ' + cauHoi).setFontWeight('bold');

  const dong = kq.replace(/\r\n/g, '\n').split('\n').map(l => l.split('\t'));
  const soCot = Math.max(...dong.map(d => d.length));
  const bang = dong.map(d => {
    const h = d.map(o => laSoThuan(o) ? Number(o) : catChoVuaO(o));
    while (h.length < soCot) h.push('');
    return h;
  });
  // Ô chữ để dạng văn bản để Sheets không tự đổi "01/02" thành ngày
  const dinhDang = bang.map(h => h.map(o => typeof o === 'number' ? 'General' : '@'));
  ws.getRange(3, 1, bang.length, soCot).setNumberFormats(dinhDang).setValues(bang);
  ws.autoResizeColumns(1, soCot);
  for (let c = 1; c <= soCot; c++) {
    if (ws.getColumnWidth(c) > 600) { ws.setColumnWidth(c, 600); ws.getRange(3, c, bang.length).setWrap(true); }
  }
  ws.activate();
  ss.toast('Xong', 'Claude', 3);
}

/**
 * Áp 1 yêu cầu cho TỪNG ô trong vùng chọn, ghi kết quả dạng GIÁ TRỊ vào cột bên
 * phải (không bị tính lại, không tốn tiền thêm). Ô bên phải đã có kết quả thì bỏ
 * qua -> nếu bị dừng giữa chừng, chạy lại sẽ làm tiếp phần còn thiếu.
 */
function claudeXuLyTungO() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActive();
  const vung = ss.getActiveRange();
  if (!vung) { ui.alert('Hãy chọn vùng ô cần xử lý trước.'); return; }

  const r = ui.prompt('Claude – xử lý từng ô',
    'Yêu cầu áp cho từng ô (kết quả ghi vào cột bên phải):\n\n' +
    'Vd: Phân loại chi phí này vào: Vật tư / Nhân công / Máy / Khác\n' +
    '    Dịch sang tiếng Anh\n    Trích mã số thuế từ đoạn văn',
    ui.ButtonSet.OK_CANCEL);
  if (r.getSelectedButton() !== ui.Button.OK) return;
  const yc = r.getResponseText().trim();
  if (!yc) return;

  const sheet = vung.getSheet();
  const vung2 = catVungCoDuLieu(vung);
  const giaTri = vung2.getDisplayValues();
  const viec = [];
  giaTri.forEach((hang, i) => hang.forEach((v, j) => {
    if (String(v).trim()) viec.push({ hang: vung2.getRow() + i, cot: vung2.getColumn() + j, v: v });
  }));
  // Bỏ qua ô mà cột bên phải đã có kết quả
  const conLai = viec.filter(x => !String(sheet.getRange(x.hang, x.cot + 1).getDisplayValue()).trim());
  if (!conLai.length) { ui.alert('Không còn ô nào cần xử lý (cột bên phải đã có kết quả).'); return; }
  if (ui.alert('Sẽ gọi Claude ' + conLai.length + ' lần. Tiếp tục?', ui.ButtonSet.YES_NO) !== ui.Button.YES) return;

  const batDau = Date.now();
  let xong = 0;
  for (let i = 0; i < conLai.length; i += SO_O_CHAY_SONG_SONG) {
    if (Date.now() - batDau > THOI_GIAN_TOI_DA_MS) {
      ui.alert('Đã xử lý ' + xong + '/' + conLai.length + ' ô thì gần hết thời gian Google cho phép.\n' +
               'Chọn lại vùng và chạy lại menu này để làm tiếp phần còn lại.');
      return;
    }
    const dot = conLai.slice(i, i + SO_O_CHAY_SONG_SONG);
    const kq = goiClaudeNhieu(dot.map(x =>
      yc + '\n\n<noi_dung>\n' + x.v + '\n</noi_dung>'), SYSTEM_O, MODEL_MAC_DINH);
    dot.forEach((x, k) => sheet.getRange(x.hang, x.cot + 1).setValue(catChoVuaO(kq[k])));
    xong += dot.length;
    SpreadsheetApp.flush();
    ss.toast('Đã xử lý ' + xong + '/' + conLai.length, 'Claude', 5);
  }
  ui.alert('Xong ' + xong + ' ô.');
}

// --------------------------------------------------------------------------
//                          GỌI API ANTHROPIC
// --------------------------------------------------------------------------

function layApiKey() {
  const k = PropertiesService.getScriptProperties().getProperty('ANTHROPIC_API_KEY');
  if (!k) throw new Error('Chưa có API key. Vào menu 🤖 Claude → Cài API key.');
  return k;
}

// Các model hỗ trợ tự chuyển sang model dự phòng khi bị từ chối (fallbacks).
function hoTroFallback(model) {
  return ['claude-opus-5-5', 'claude-opus-5', 'claude-sonnet-5-5',
          'claude-fable-5-2', 'claude-fable-5-1'].indexOf(String(model).toLowerCase()) >= 0;
}

function taoYeuCau(userText, systemPrompt, model) {
  const fb = hoTroFallback(model);
  const headers = {
    'x-api-key': layApiKey(),
    'anthropic-version': API_VERSION,
  };
  const body = {
    model: model,
    max_tokens: MAX_TOKENS,
    output_config: { effort: EFFORT },
    system: systemPrompt,
    messages: [{ role: 'user', content: userText }],
  };
  if (fb) {
    headers['anthropic-beta'] = 'server-side-fallback-2026-07-01';
    body.fallbacks = 'default';
  }
  return {
    url: API_URL,
    method: 'post',
    contentType: 'application/json',
    headers: headers,
    payload: JSON.stringify(body),
    muteHttpExceptions: true,
  };
}

function docKetQua(resp) {
  const status = resp.getResponseCode();
  let j = null;
  try { j = JSON.parse(resp.getContentText('UTF-8')); } catch (e) { /* không phải JSON */ }
  if (status !== 200) {
    const msg = 'HTTP ' + status + (j && j.error ? ' - ' + j.error.message : '');
    if (status === 401) throw new Error('API key không đúng (' + msg + ')');
    if (status === 429) throw new Error('Vượt giới hạn gọi, thử lại sau (' + msg + ')');
    if (status === 529) throw new Error('Máy chủ Claude đang quá tải (' + msg + ')');
    throw new Error(msg);
  }
  const text = (j.content || []).filter(b => b.type === 'text').map(b => b.text).join('');
  if (j.stop_reason === 'refusal') throw new Error('Claude từ chối yêu cầu này');
  if (j.stop_reason === 'max_tokens') return text.trim() + ' […bị cắt do vượt max_tokens]';
  return text.trim();
}

function canThuLai(status) { return status === 429 || status >= 500; }

/** Gọi 1 yêu cầu, thử lại khi 429/5xx. */
function goiClaude(userText, systemPrompt, model, soLan) {
  const req = taoYeuCau(userText, systemPrompt, model);
  let resp;
  for (let lan = 1; lan <= soLan; lan++) {
    resp = UrlFetchApp.fetch(req.url, req);
    if (!canThuLai(resp.getResponseCode()) || lan === soLan) break;
    Utilities.sleep(2000 * lan);
  }
  return docKetQua(resp);
}

/** Gọi song song nhiều yêu cầu; trả về mảng kết quả (lỗi thành "#CLAUDE: ..."). */
function goiClaudeNhieu(texts, systemPrompt, model) {
  const reqs = texts.map(t => taoYeuCau(t, systemPrompt, model));
  const kq = new Array(texts.length);
  let canGoi = reqs.map((_, i) => i);
  for (let lan = 1; lan <= 3 && canGoi.length; lan++) {
    const resps = UrlFetchApp.fetchAll(canGoi.map(i => reqs[i]));
    const thuLai = [];
    resps.forEach((resp, k) => {
      const i = canGoi[k];
      if (canThuLai(resp.getResponseCode()) && lan < 3) { thuLai.push(i); return; }
      try { kq[i] = docKetQua(resp); } catch (e) { kq[i] = '#CLAUDE: ' + e.message; }
    });
    canGoi = thuLai;
    if (canGoi.length) Utilities.sleep(3000 * lan);
  }
  return kq;
}

// --------------------------------------------------------------------------
//                              TIỆN ÍCH
// --------------------------------------------------------------------------

/** Ô / vùng (mảng 2 chiều) / giá trị -> chữ; vùng -> bảng TSV. */
function giaTriThanhChu(v) {
  if (Array.isArray(v)) {
    const hang = v.map(h => (Array.isArray(h) ? h : [h]).map(motGiaTri).join('\t'));
    // Bỏ các dòng trống ở cuối (khi chọn cả cột A:A)
    while (hang.length && !hang[hang.length - 1].replace(/\t/g, '')) hang.pop();
    return hang.join('\n');
  }
  return motGiaTri(v);
}

function motGiaTri(v) {
  if (v === null || v === undefined) return '';
  if (v instanceof Date) {
    const tz = Session.getScriptTimeZone();
    const coGio = v.getHours() || v.getMinutes();
    return Utilities.formatDate(v, tz, coGio ? 'dd/MM/yyyy HH:mm' : 'dd/MM/yyyy');
  }
  // Tab/xuống dòng trong ô sẽ làm vỡ bảng -> thay bằng khoảng trắng
  return String(v).replace(/[\t\r\n]+/g, ' ');
}

/** Chọn cả cột/hàng -> chỉ lấy phần có dữ liệu. */
function catVungCoDuLieu(vung) {
  const sh = vung.getSheet();
  const lastRow = Math.min(vung.getLastRow(), sh.getLastRow());
  const lastCol = Math.min(vung.getLastColumn(), sh.getLastColumn());
  if (lastRow < vung.getRow() || lastCol < vung.getColumn()) return vung.getCell(1, 1);
  return sh.getRange(vung.getRow(), vung.getColumn(),
    lastRow - vung.getRow() + 1, lastCol - vung.getColumn() + 1);
}

/** Số dạng 1234 / -1234.5 (không số 0 đứng đầu như mã "0123"). */
function laSoThuan(s) {
  s = String(s).trim();
  return s.length > 0 && s.length <= 15 && /^-?(0|[1-9]\d*)(\.\d+)?$/.test(s);
}

function catChoVuaO(s) {
  s = String(s);
  return s.length > GIOI_HAN_O ? s.slice(0, GIOI_HAN_O - 20) + ' […còn nữa]' : s;
}

function bam(s) {
  return Utilities.base64EncodeWebSafe(
    Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, s, Utilities.Charset.UTF_8));
}
