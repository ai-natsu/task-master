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

# 旧Web版はTailwindの既定sans-serifスタック(Windows上ではSegoe UIに解決)。
# CustomTkinter既定の"Roboto"のままだと混在して見た目が揃わないため統一する。
FONT_FAMILY = "Segoe UI"
