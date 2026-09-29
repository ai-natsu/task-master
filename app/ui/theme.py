"""アプリ共通の配色定数。

CustomTkinterの既定テーマはグレー寄りで、カード同士のコントラストが弱く
「古く・薄く」見えやすい。旧Web版(Tailwind)のスレート/インディゴ配色に寄せ、
背景とカードのコントラストをはっきりさせる。(light, dark) のタプルは
CustomTkinterのfg_color等にそのまま渡せる。
"""

BG = ("#f8fafc", "#0f172a")            # アプリ全体の背景 (slate-50 / slate-950)
SIDEBAR_BG = ("#ffffff", "#111827")     # サイドバー背景 (white / gray-900)
CARD_BG = ("#ffffff", "#1e293b")        # カード背景 (white / slate-800)
CARD_BORDER = ("#e2e8f0", "#334155")    # カード枠線 (slate-200 / slate-700)
SUBTLE_BG = ("#f1f5f9", "#1e293b")      # カンバン列など、bgより一段濃い背景

TEXT_PRIMARY = ("#0f172a", "#f1f5f9")   # 本文 (slate-900 / slate-100)
TEXT_MUTED = ("#64748b", "#94a3b8")     # 補助テキスト (slate-500 / slate-400)

ACCENT = "#6366f1"       # indigo-500（主要アクション）
ACCENT_HOVER = "#4f46e5"  # indigo-600

# UIは全て日本語のため、日本語グリフを持つゴシック体を直接指定する。
# "Segoe UI"はASCII/欧文専用フォントで日本語グリフを持たず、Windowsが
# 自動的に別フォントへ代替表示する際、環境によっては明朝体(serif)が
# 選ばれてしまい意図せず古い見た目になる（実機検証で確認）。
# "Yu Gothic UI" はWindows 10/11の日本語UI既定フォントで、この代替の
# 揺れが起きず、欧文・数字も違和感なく表示できる。
FONT_FAMILY = "Yu Gothic UI"
