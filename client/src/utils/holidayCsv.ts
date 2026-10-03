export interface HolidayRow {
  date: string;
  name: string;
}

/** CSV のバイト列を文字列にする。UTF-8 → Shift_JIS の順に試し、どちらも不可なら null。 */
export function decodeCsv(buffer: ArrayBuffer): string | null {
  for (const encoding of ["utf-8", "shift_jis"]) {
    try {
      return new TextDecoder(encoding, { fatal: true }).decode(buffer);
    } catch {
      // 次の文字コードを試す
    }
  }
  return null;
}

/** "YYYY-MM-DD" / "YYYY/M/D" を "YYYY-MM-DD" にする。解釈できなければ null。 */
export function parseDate(text: string): string | null {
  const m = /^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/.exec(text.trim());
  if (!m) return null;
  const [year, month, day] = [Number(m[1]), Number(m[2]), Number(m[3])];
  const d = new Date(Date.UTC(year, month - 1, day));
  if (d.getUTCFullYear() !== year || d.getUTCMonth() !== month - 1 || d.getUTCDate() !== day) return null;
  return `${m[1]}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

/** 引用符・\r\n / \n / \r の改行に対応した最小限の CSV 分割。 */
export function splitCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;
  const body = text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;

  for (let i = 0; i < body.length; i++) {
    const c = body[i];
    if (quoted) {
      if (c === '"' && body[i + 1] === '"') {
        cell += '"';
        i++;
      } else if (c === '"') {
        quoted = false;
      } else {
        cell += c;
      }
    } else if (c === '"') {
      quoted = true;
    } else if (c === ",") {
      row.push(cell);
      cell = "";
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && body[i + 1] === "\n") i++;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += c;
    }
  }
  if (cell !== "" || row.length > 0) {
    row.push(cell);
    rows.push(row);
  }
  return rows;
}

/**
 * 祝日 CSV（列順「日付, 名称」）を行に変換する。日付が解釈できない行（ヘッダー）や
 * 名称が空の行は読み飛ばす。文字コードを判定できなければ null。
 */
export function parseHolidayCsv(buffer: ArrayBuffer): HolidayRow[] | null {
  const text = decodeCsv(buffer);
  if (text === null) return null;
  const rows: HolidayRow[] = [];
  for (const cells of splitCsv(text)) {
    if (cells.length < 2) continue;
    const date = parseDate(cells[0]);
    const name = cells[1].trim();
    if (date === null || !name) continue;
    rows.push({ date, name });
  }
  return rows;
}
