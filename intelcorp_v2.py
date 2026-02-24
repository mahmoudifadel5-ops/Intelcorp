# ============================================================
# INTELCORP — Company Intelligence Tool v2
# Fadel Mahmoudi
# ============================================================
# pip3 install dash requests groq
# export GROQ_API_KEY="gsk_..."
# python3 intelcorp_v2.py → http://127.0.0.1:8051
# ============================================================

import os, requests, json
from datetime import datetime
from dash import Dash, dcc, html, Input, Output, State, no_update, ctx, ALL
from groq import Groq

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

FLAGS = {
    "us":"🇺🇸","gb":"🇬🇧","fr":"🇫🇷","de":"🇩🇪","ch":"🇨🇭","nl":"🇳🇱","sg":"🇸🇬",
    "ae":"🇦🇪","ru":"🇷🇺","cn":"🇨🇳","sn":"🇸🇳","ma":"🇲🇦","ci":"🇨🇮","lu":"🇱🇺",
    "be":"🇧🇪","au":"🇦🇺","ca":"🇨🇦","jp":"🇯🇵","in":"🇮🇳","br":"🇧🇷","za":"🇿🇦",
    "ng":"🇳🇬","ky":"🇰🇾","ie":"🇮🇪","se":"🇸🇪","no":"🇳🇴","it":"🇮🇹","es":"🇪🇸",
    "bm":"🇧🇲","vg":"🇻🇬","pa":"🇵🇦","gh":"🇬🇭","ke":"🇰🇪","eg":"🇪🇬","dz":"🇩🇿",
}
NAMES = {
    "us":"États-Unis","gb":"Royaume-Uni","fr":"France","de":"Allemagne","ch":"Suisse",
    "nl":"Pays-Bas","sg":"Singapour","ae":"Émirats Arabes Unis","ru":"Russie","cn":"Chine",
    "sn":"Sénégal","ma":"Maroc","ci":"Côte d'Ivoire","lu":"Luxembourg","be":"Belgique",
    "au":"Australie","ca":"Canada","jp":"Japon","in":"Inde","br":"Brésil",
    "za":"Afrique du Sud","ng":"Nigéria","ky":"Îles Caïmans","ie":"Irlande",
    "se":"Suède","no":"Norvège","it":"Italie","es":"Espagne","bm":"Bermudes",
}

# ── CSS Global injecté via index_string ─────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Playfair+Display:wght@400;600&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --bg: #06070f;
    --bg2: #090b18;
    --bg3: #0d1022;
    --border: #181b30;
    --border2: #222540;
    --gold: #c8a951;
    --gold2: #e8c96a;
    --text: #d0d0e0;
    --text2: #888899;
    --text3: #444455;
    --green: #00cc66;
    --red: #ff4455;
    --orange: #ff8c00;
    --mono: 'DM Mono', monospace;
    --serif: 'Playfair Display', Georgia, serif;
}

body { background: var(--bg); color: var(--text); font-family: var(--mono); }
::-webkit-scrollbar { width: 4px; } 
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

.search-input:focus { border-color: var(--gold) !important; }
.search-input::placeholder { color: var(--text3) !important; }

.row-btn:hover { background: var(--gold) !important; color: var(--bg) !important; }
.analyze-btn:hover { background: #b8992f !important; }

.result-row:hover { background: rgba(200,169,81,0.04) !important; }

.tag { display:inline-block; padding:2px 8px; border-radius:2px; font-size:9px; letter-spacing:2px; font-weight:500; }
.tag-green { background:rgba(0,204,102,0.1); color:var(--green); border:1px solid rgba(0,204,102,0.2); }
.tag-red { background:rgba(255,68,85,0.1); color:var(--red); border:1px solid rgba(255,68,85,0.2); }
.tag-orange { background:rgba(255,140,0,0.1); color:var(--orange); border:1px solid rgba(255,140,0,0.2); }
.tag-gold { background:rgba(200,169,81,0.1); color:var(--gold); border:1px solid rgba(200,169,81,0.2); }

@keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.fade-in { animation: fadeIn 0.3s ease forwards; }

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.loading { animation: pulse 1.2s ease infinite; }
"""

# ── DATA ────────────────────────────────────────────────────

def live_search(query, country_filter=""):
    if not query or len(query) < 2:
        return [], "opencorporates"
    try:
        url = f"https://api.opencorporates.com/v0.4/companies/search?q={requests.utils.quote(query)}&per_page=12"
        if country_filter:
            url += f"&jurisdiction_code={country_filter}"
        r = requests.get(url, timeout=6, headers=HEADERS)
        if r.status_code == 200:
            companies = r.json().get("results", {}).get("companies", [])
            if companies:
                results = []
                for c in companies:
                    co = c.get("company", {})
                    jcode = co.get("jurisdiction_code", "").lower()
                    cc = jcode.split("_")[0]
                    addr = co.get("registered_address", {})
                    city = (addr.get("city") or addr.get("locality") or "") if isinstance(addr, dict) else ""
                    results.append({
                        "nom": co.get("name", ""),
                        "numero": co.get("company_number", ""),
                        "cc": cc, "pays": NAMES.get(cc, jcode.upper()),
                        "flag": FLAGS.get(cc, "🏳️"),
                        "statut": co.get("current_status", ""),
                        "date": co.get("incorporation_date", ""),
                        "ville": city,
                        "type": co.get("company_type", ""),
                        "url": co.get("opencorporates_url", ""),
                    })
                return results, "opencorporates"
    except: pass

    # Fallback Groq
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        prompt = f'List real companies matching "{query}"{f" in {country_filter}" if country_filter else ""}. Return ONLY JSON array max 10: [{{"nom":"","pays":"","pays_code":"2-letter ISO","ville":"","secteur":"","statut":"Active","type":"","date_creation":""}}]'
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.1, max_tokens=1000,
        )
        text = resp.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        raw = json.loads(text.strip().rstrip("```"))
        results = []
        for co in raw:
            cc = co.get("pays_code","").lower()[:2]
            results.append({
                "nom": co.get("nom",""), "numero": "—",
                "cc": cc, "pays": co.get("pays",""),
                "flag": FLAGS.get(cc,"🏳️"),
                "statut": co.get("statut","Active"),
                "date": co.get("date_creation",""),
                "ville": co.get("ville",""),
                "type": co.get("type","") or co.get("secteur",""),
                "url": "",
            })
        return results, "groq"
    except Exception as e:
        print(f"Groq suggest error: {e}")
    return [], "none"

def ai_research(company_name, country=""):
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        prompt = f"""Expert due diligence analyst, commodity trading. Research "{company_name}" {f"from {country}" if country else ""}.
Return ONLY valid JSON:
{{"nom_complet":"","description":"","pays":"","ville_siege":"","adresse":"","site_web":"","email_contact":"","telephone":"","date_creation":"","forme_juridique":"","numero_enregistrement":"","secteur":"","activite_principale":"","produits_services":[],"marches_operes":[],"dirigeants":[{{"nom":"","poste":"","nationalite":"","depuis":"","parcours_anterieur":""}}],"actionnaires":[{{"nom":"","pourcentage":"","type":""}}],"filiales":[],"maison_mere":"","partenaires_connus":[],"financier":{{"chiffre_affaires":"","benefice_net":"","capitalisation_boursiere":"","effectifs":"","notation_credit":"","bourse_cotation":"","ticker":""}},"reputation":{{"positif":[],"negatif":[],"controverses":[],"certifications":[]}},"presence_digitale":{{"linkedin":"","twitter":"","wikipedia":""}},"sanctions":{{"ofac":"","ue":"","onu":"","commentaire":""}},"red_flags":[{{"niveau":"rouge|orange|vert","titre":"","detail":""}}],"score_risque":0,"niveau_risque":"FAIBLE|MODERE|ELEVE","verdict":"","recommandations":[]}}"""
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.2, max_tokens=4000,
        )
        text = resp.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        return json.loads(text.strip().rstrip("```"))
    except Exception as e:
        print(f"Groq error: {e}")
        return None

def check_sanctions(name):
    try:
        r = requests.get(f"https://api.opensanctions.org/search/default?q={requests.utils.quote(name)}&schema=Company", timeout=8)
        if r.status_code == 200:
            d = r.json()
            return d.get("total",{}).get("value",0), d.get("results",[])[:5]
    except: pass
    return 0, []

def check_persons(name):
    try:
        r = requests.get(f"https://api.opensanctions.org/search/default?q={requests.utils.quote(name)}&schema=Person", timeout=8)
        if r.status_code == 200:
            d = r.json()
            return d.get("total",{}).get("value",0), d.get("results",[])[:5]
    except: pass
    return 0, []

# ── APP ─────────────────────────────────────────────────────

app = Dash(__name__, suppress_callback_exceptions=True)

app.index_string = f'''<!DOCTYPE html>
<html>
<head>
    {{%metas%}}
    <title>IntelCorp — Company Intelligence</title>
    {{%favicon%}}
    {{%css%}}
    <style>{CUSTOM_CSS}</style>
</head>
<body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
</body>
</html>'''

app.layout = html.Div(style={"backgroundColor":"var(--bg)","minHeight":"100vh","fontFamily":"var(--mono)"}, children=[

    # ── NAVBAR ──────────────────────────────────────────────
    html.Div(style={
        "backgroundColor":"var(--bg2)","borderBottom":"1px solid var(--border)",
        "padding":"0 40px","height":"56px","display":"flex",
        "justifyContent":"space-between","alignItems":"center",
        "position":"sticky","top":"0","zIndex":"100",
    }, children=[
        html.Div(style={"display":"flex","alignItems":"center","gap":"12px"}, children=[
            html.Div(style={
                "width":"28px","height":"28px","background":"var(--gold)",
                "borderRadius":"50%","display":"flex","alignItems":"center",
                "justifyContent":"center","fontSize":"14px","color":"var(--bg)","fontWeight":"bold"
            }, children="I"),
            html.Div(style={"display":"flex","gap":"1px"}, children=[
                html.Span("Intel", style={"color":"#fff","fontSize":"15px","fontFamily":"var(--serif)","fontWeight":"600","letterSpacing":"0.5px"}),
                html.Span("Corp", style={"color":"var(--gold)","fontSize":"15px","fontFamily":"var(--serif)","fontWeight":"600","letterSpacing":"0.5px"}),
            ]),
            html.Div("BETA", style={"fontSize":"8px","letterSpacing":"2px","color":"var(--text3)","border":"1px solid var(--border2)","padding":"2px 6px","borderRadius":"2px","marginLeft":"5px"}),
        ]),
        html.Div(style={"display":"flex","gap":"30px","alignItems":"center"}, children=[
            html.Div("COMMODITY · DUE DILIGENCE · GROQ AI", style={"color":"var(--text3)","fontSize":"9px","letterSpacing":"3px"}),
        ]),
    ]),

    # ── HERO ────────────────────────────────────────────────
    html.Div(style={
        "padding":"70px 40px 50px",
        "background":"linear-gradient(160deg, #0c0f26 0%, var(--bg) 60%)",
        "borderBottom":"1px solid var(--border)",
        "position":"relative","overflow":"hidden",
    }, children=[
        # Fond décoratif
        html.Div(style={
            "position":"absolute","top":"-100px","right":"-100px",
            "width":"400px","height":"400px","borderRadius":"50%",
            "background":"radial-gradient(circle, rgba(200,169,81,0.06) 0%, transparent 70%)",
            "pointerEvents":"none",
        }),

        html.Div(style={"maxWidth":"700px","position":"relative"}, children=[
            html.Div("DUE DILIGENCE PLATFORM", style={
                "color":"var(--gold)","fontSize":"10px","letterSpacing":"5px",
                "marginBottom":"16px","fontWeight":"500",
            }),
            html.H1(style={
                "fontFamily":"var(--serif)","fontWeight":"600","fontSize":"42px",
                "color":"#fff","lineHeight":"1.15","marginBottom":"12px","letterSpacing":"-0.5px",
            }, children=[
                "Company Intelligence",
                html.Br(),
                html.Span("& Risk Assessment", style={"color":"var(--text2)","fontSize":"34px"}),
            ]),
            html.P("Recherche instantanée · Dirigeants · Sanctions · Registres officiels · Score de risque IA",
                style={"color":"var(--text3)","fontSize":"12px","letterSpacing":"1.5px","marginBottom":"40px"}),

            # SEARCH BAR
            html.Div(style={"display":"flex","gap":"0","marginBottom":"12px"}, children=[
                html.Div("⌕", style={
                    "backgroundColor":"var(--bg3)","border":"1px solid var(--border2)",
                    "borderRight":"none","padding":"0 18px","display":"flex",
                    "alignItems":"center","fontSize":"20px","color":"var(--text3)",
                    "borderRadius":"4px 0 0 4px",
                }),
                dcc.Input(
                    id="company-input", type="text",
                    placeholder="Rechercher une société... ex: Glencore, Rosneft, Microsoft",
                    debounce=False, n_submit=0,
                    className="search-input",
                    style={
                        "flex":"1","backgroundColor":"var(--bg3)",
                        "border":"1px solid var(--border2)","borderLeft":"none","borderRight":"none",
                        "color":"#fff","padding":"16px 20px","fontSize":"15px",
                        "outline":"none","fontFamily":"var(--mono)",
                        "transition":"border-color 0.2s",
                    }
                ),
                dcc.Dropdown(
                    id="filter-country",
                    options=[
                        {"label":"🌍  Tous pays","value":""},
                        {"label":"🇫🇷  France","value":"fr"},{"label":"🇬🇧  Royaume-Uni","value":"gb"},
                        {"label":"🇺🇸  États-Unis","value":"us"},{"label":"🇨🇭  Suisse","value":"ch"},
                        {"label":"🇩🇪  Allemagne","value":"de"},{"label":"🇳🇱  Pays-Bas","value":"nl"},
                        {"label":"🇸🇬  Singapour","value":"sg"},{"label":"🇦🇪  Émirats","value":"ae"},
                        {"label":"🇷🇺  Russie","value":"ru"},{"label":"🇨🇳  Chine","value":"cn"},
                        {"label":"🇸🇳  Sénégal","value":"sn"},{"label":"🇲🇦  Maroc","value":"ma"},
                        {"label":"🇨🇮  Côte d'Ivoire","value":"ci"},{"label":"🇰🇾  Îles Caïmans","value":"ky"},
                        {"label":"🇱🇺  Luxembourg","value":"lu"},{"label":"🇳🇬  Nigéria","value":"ng"},
                    ],
                    value="", clearable=False,
                    style={"width":"200px","borderRadius":"0","fontFamily":"var(--mono)"},
                ),
                html.Button("ANALYSER", id="search-btn", n_clicks=0,
                    className="analyze-btn",
                    style={
                        "backgroundColor":"var(--gold)","color":"var(--bg)","border":"none",
                        "padding":"0 28px","fontSize":"11px","letterSpacing":"2px",
                        "cursor":"pointer","fontFamily":"var(--mono)","fontWeight":"500",
                        "borderRadius":"0 4px 4px 0","transition":"background 0.2s","whiteSpace":"nowrap",
                    }),
            ]),
            html.Div(id="search-status", style={"color":"var(--text3)","fontSize":"10px","letterSpacing":"1px","height":"16px"}),
        ]),
    ]),

    # ── RESULTS ─────────────────────────────────────────────
    html.Div(style={"maxWidth":"1200px","margin":"0 auto","padding":"30px 40px"}, children=[
        html.Div(id="live-results"),
        html.Div(id="analysis-result"),
    ]),
])

# ── CALLBACK 1 : Live search ─────────────────────────────────

@app.callback(
    Output("live-results","children"),
    Output("search-status","children"),
    Input("company-input","value"),
    Input("filter-country","value"),
    prevent_initial_call=True
)
def update_live(query, country):
    if not query or len(query.strip()) < 2:
        return html.Div(), ""

    results, source = live_search(query.strip(), country or "")

    if not results:
        return html.Div(style={"textAlign":"center","padding":"40px","color":"var(--text3)","fontSize":"13px"}, children=[
            html.Div("○", style={"fontSize":"30px","marginBottom":"10px"}),
            html.Div(f"Aucun résultat pour « {query} »"),
        ]), "0 résultat"

    source_label = "OPENCORPORATES" if source == "opencorporates" else "GROQ AI"
    source_color = "#4a9eff" if source == "opencorporates" else "var(--gold)"

    rows = []
    for co in results:
        s = co.get("statut","").lower()
        if "active" in s: sc, sl, stag = "var(--green)", "ACTIVE", "tag-green"
        elif "dissolved" in s or "struck" in s: sc, sl, stag = "var(--red)", "DISSOUTE", "tag-red"
        else: sc, sl, stag = "var(--orange)", s.upper()[:10] or "—", "tag-orange"

        rows.append(html.Div(className="result-row", style={
            "display":"flex","justifyContent":"space-between","alignItems":"center",
            "padding":"14px 20px","borderBottom":"1px solid var(--border)",
            "transition":"background 0.15s","cursor":"default",
        }, children=[
            html.Div(style={"display":"flex","alignItems":"center","gap":"16px","flex":"1"}, children=[
                html.Div(co.get("flag","🏳️"), style={"fontSize":"26px","lineHeight":"1","minWidth":"34px","textAlign":"center"}),
                html.Div(style={"flex":"1"}, children=[
                    html.Div(co.get("nom",""), style={"color":"#fff","fontSize":"14px","fontWeight":"500","marginBottom":"4px","letterSpacing":"0.3px"}),
                    html.Div(style={"display":"flex","gap":"16px","flexWrap":"wrap","alignItems":"center"}, children=[
                        html.Span(f"📍 {co.get('pays','')} {('· '+co.get('ville','')) if co.get('ville') else ''}", style={"color":"var(--text2)","fontSize":"11px"}),
                        html.Span(f"🏢 {co.get('type','')[:32]}", style={"color":"var(--text3)","fontSize":"11px"}) if co.get("type") else html.Span(),
                        html.Span(f"📅 {co.get('date','')}", style={"color":"var(--text3)","fontSize":"11px"}) if co.get("date") else html.Span(),
                        html.Span(f"#{co.get('numero','')}", style={"color":"var(--border2)","fontSize":"10px"}) if co.get("numero") and co.get("numero") != "—" else html.Span(),
                    ]),
                ]),
            ]),
            html.Div(style={"display":"flex","alignItems":"center","gap":"12px","marginLeft":"20px"}, children=[
                html.Span(sl, className=f"tag {stag}"),
                html.Button("ANALYSER →",
                    id={"type":"row-btn","index":f"{co.get('nom','')}||{co.get('pays','')}"},
                    n_clicks=0, className="row-btn",
                    style={
                        "backgroundColor":"transparent","color":"var(--gold)",
                        "border":"1px solid rgba(200,169,81,0.4)","padding":"7px 16px",
                        "fontSize":"10px","letterSpacing":"1.5px","cursor":"pointer",
                        "fontFamily":"var(--mono)","borderRadius":"3px","transition":"all 0.2s",
                        "whiteSpace":"nowrap",
                    }),
            ]),
        ]))

    return html.Div(className="fade-in", style={
        "backgroundColor":"var(--bg2)","border":"1px solid var(--border)",
        "borderRadius":"6px","overflow":"hidden","marginBottom":"24px",
    }, children=[
        html.Div(style={
            "padding":"12px 20px","borderBottom":"1px solid var(--border)",
            "display":"flex","justifyContent":"space-between","alignItems":"center",
        }, children=[
            html.Div(style={"display":"flex","alignItems":"center","gap":"10px"}, children=[
                html.Span(f"{len(results)} SOCIÉTÉS TROUVÉES", style={"color":"var(--gold)","fontSize":"9px","letterSpacing":"3px","fontWeight":"500"}),
                html.Span(source_label, style={"color":source_color,"fontSize":"8px","letterSpacing":"2px","border":f"1px solid {source_color}","padding":"2px 7px","borderRadius":"2px","opacity":"0.7"}),
            ]),
            html.Span("Cliquez sur ANALYSER pour la fiche complète", style={"color":"var(--text3)","fontSize":"10px"}),
        ]),
        html.Div(rows),
    ]), f"✓ {len(results)} résultat(s) · source: {source_label}"


# ── CALLBACK 2 : Analyse complète ───────────────────────────

@app.callback(
    Output("analysis-result","children"),
    Input({"type":"row-btn","index":ALL},"n_clicks"),
    Input("search-btn","n_clicks"),
    State({"type":"row-btn","index":ALL},"id"),
    State("company-input","value"),
    prevent_initial_call=True
)
def analyze(row_clicks, btn_clicks, ids, input_value):
    triggered = ctx.triggered_id

    # Bouton ANALYSER principal
    if triggered == "search-btn":
        if not input_value or not input_value.strip():
            return no_update
        name, country = input_value.strip(), ""
    # Bouton ANALYSER d'une ligne
    elif isinstance(triggered, dict) and triggered.get("type") == "row-btn":
        if not any(n for n in row_clicks if n):
            return no_update
        raw = triggered.get("index","")
        parts = raw.split("||")
        name, country = parts[0], (parts[1] if len(parts) > 1 else "")
    else:
        return no_update

    ai = ai_research(name, country)
    sc_count, sc_hits = check_sanctions(name)
    pe_count, pe_hits = check_persons(name)

    if not ai:
        return html.Div("Erreur analyse IA — vérifiez votre GROQ_API_KEY", style={"color":"var(--red)","padding":"20px"})

    score = ai.get("score_risque", 0)
    if sc_count > 0: score = max(score, 75)
    niveau = "ELEVE" if sc_count > 0 else ai.get("niveau_risque","MODERE")
    cmap = {"ELEVE":"var(--red)","MODERE":"var(--orange)","FAIBLE":"var(--green)"}
    couleur = cmap.get(niveau,"var(--orange)")

    # Helpers
    def section(title, children, accent="var(--gold)"):
        return html.Div(style={
            "backgroundColor":"var(--bg2)","border":"1px solid var(--border)",
            "borderRadius":"6px","padding":"22px 26px","marginBottom":"16px",
        }, children=[
            html.Div(title, style={"color":accent,"fontSize":"9px","letterSpacing":"4px",
                "fontWeight":"500","marginBottom":"18px","paddingBottom":"10px",
                "borderBottom":"1px solid var(--border)"}),
            *children,
        ])

    def info_row(label, val, highlight=False):
        if not val or str(val).strip() in ["","null","None"]: return html.Div()
        return html.Div(style={"display":"flex","padding":"8px 0","borderBottom":"1px solid var(--border)"}, children=[
            html.Div(label, style={"color":"var(--text3)","fontSize":"11px","minWidth":"210px","letterSpacing":"0.5px"}),
            html.Div(str(val), style={"color":"var(--gold)" if highlight else "var(--text)","fontSize":"12px","flex":"1","letterSpacing":"0.3px"}),
        ])

    # ── SCORE HEADER ──
    score_section = html.Div(className="fade-in", style={
        "backgroundColor":"var(--bg2)","border":f"1px solid var(--border)",
        "borderTop":f"3px solid {couleur}","borderRadius":"6px",
        "padding":"28px 30px","marginBottom":"16px",
    }, children=[
        html.Div(style={"display":"flex","justifyContent":"space-between","alignItems":"flex-start"}, children=[
            html.Div(style={"flex":"1"}, children=[
                html.Div(ai.get("pays","").upper() + "  ·  " + ai.get("secteur","").upper(),
                    style={"color":"var(--text3)","fontSize":"9px","letterSpacing":"3px","marginBottom":"10px"}),
                html.H2(ai.get("nom_complet", name), style={
                    "fontFamily":"var(--serif)","color":"#fff","fontSize":"28px",
                    "fontWeight":"600","marginBottom":"8px","letterSpacing":"-0.3px",
                }),
                html.P(ai.get("description",""), style={
                    "color":"var(--text2)","fontSize":"13px","lineHeight":"1.7",
                    "maxWidth":"600px","fontStyle":"italic",
                }),
            ]),
            html.Div(style={"textAlign":"right","paddingLeft":"30px","minWidth":"160px"}, children=[
                html.Div("RISK ASSESSMENT", style={"color":"var(--text3)","fontSize":"8px","letterSpacing":"3px","marginBottom":"6px"}),
                html.Div(niveau, style={"color":couleur,"fontSize":"30px","fontFamily":"var(--serif)","fontWeight":"600","marginBottom":"4px"}),
                html.Div(style={"display":"flex","alignItems":"center","gap":"8px","justifyContent":"flex-end"}, children=[
                    html.Div(style={"flex":"1","height":"4px","background":"var(--border)","borderRadius":"2px","overflow":"hidden"}, children=[
                        html.Div(style={"height":"100%","width":f"{score}%","background":couleur,"borderRadius":"2px","transition":"width 1s ease"})
                    ]),
                    html.Div(f"{score}/100", style={"color":"var(--text3)","fontSize":"10px","whiteSpace":"nowrap"}),
                ]),
            ]),
        ]),
    ])

    # ── GRILLE 2 COL ──
    grid = html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px","marginBottom":"16px"}, children=[
        section("IDENTITÉ LÉGALE", [
            info_row("Pays", ai.get("pays")),
            info_row("Ville / Siège", ai.get("ville_siege")),
            info_row("Adresse", ai.get("adresse")),
            info_row("Date de création", ai.get("date_creation")),
            info_row("Forme juridique", ai.get("forme_juridique")),
            info_row("N° enregistrement", ai.get("numero_enregistrement")),
            info_row("Site web", ai.get("site_web"), True),
            info_row("Email", ai.get("email_contact")),
            info_row("Téléphone", ai.get("telephone")),
            info_row("Activité principale", ai.get("activite_principale")),
            info_row("Maison mère", ai.get("maison_mere")),
            info_row("Filiales", ", ".join(ai.get("filiales",[])[:4])),
        ]),
        html.Div([
            section("DONNÉES FINANCIÈRES", [
                info_row("Chiffre d'affaires", ai.get("financier",{}).get("chiffre_affaires"), True),
                info_row("Bénéfice net", ai.get("financier",{}).get("benefice_net")),
                info_row("Capitalisation boursière", ai.get("financier",{}).get("capitalisation_boursiere")),
                info_row("Effectifs", ai.get("financier",{}).get("effectifs")),
                info_row("Notation crédit", ai.get("financier",{}).get("notation_credit")),
                info_row("Cotation", ai.get("financier",{}).get("bourse_cotation")),
                info_row("Ticker", ai.get("financier",{}).get("ticker")),
            ]),
            section("PRÉSENCE DIGITALE", [
                info_row("LinkedIn", ai.get("presence_digitale",{}).get("linkedin"), True),
                info_row("Twitter/X", ai.get("presence_digitale",{}).get("twitter")),
                info_row("Wikipedia", ai.get("presence_digitale",{}).get("wikipedia")),
            ]),
        ]),
    ])

    # ── DIRIGEANTS ──
    dirs = [d for d in ai.get("dirigeants",[]) if d.get("nom")]
    dir_section = html.Div()
    if dirs:
        dir_cards = [html.Div(style={
            "backgroundColor":"var(--bg)","border":"1px solid var(--border)",
            "borderRadius":"5px","padding":"16px","position":"relative",
        }, children=[
            html.Div(style={"display":"flex","justifyContent":"space-between","alignItems":"flex-start","marginBottom":"6px"}, children=[
                html.Div(d.get("nom",""), style={"color":"#fff","fontSize":"14px","fontWeight":"500"}),
                html.Span(d.get("poste",""), className="tag tag-gold"),
            ]),
            html.Div(d.get("parcours_anterieur",""), style={"color":"var(--text3)","fontSize":"11px","marginBottom":"8px","lineHeight":"1.5"}),
            html.Div(style={"display":"flex","gap":"16px"}, children=[
                html.Span(f"🌍 {d.get('nationalite','—')}", style={"color":"var(--text3)","fontSize":"10px"}),
                html.Span(f"📅 Depuis {d.get('depuis','—')}", style={"color":"var(--text3)","fontSize":"10px"}),
            ]),
        ]) for d in dirs[:6]]
        dir_section = section("DIRIGEANTS", [
            html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"10px"}, children=dir_cards)
        ])

    # ── ACTIONNAIRES ──
    acts = [a for a in ai.get("actionnaires",[]) if a.get("nom")]
    act_section = html.Div()
    if acts:
        act_cards = [html.Div(style={
            "backgroundColor":"var(--bg)","border":"1px solid var(--border)",
            "borderRadius":"5px","padding":"14px 18px","textAlign":"center","minWidth":"130px",
        }, children=[
            html.Div(a.get("nom",""), style={"color":"var(--text)","fontSize":"12px","fontWeight":"500","marginBottom":"4px"}),
            html.Div(a.get("pourcentage",""), style={"color":"var(--gold)","fontSize":"20px","fontFamily":"var(--serif)","fontWeight":"600","marginBottom":"2px"}),
            html.Span(a.get("type",""), className="tag tag-gold"),
        ]) for a in acts[:8]]
        act_section = section("ACTIONNARIAT", [
            html.Div(style={"display":"flex","gap":"10px","flexWrap":"wrap"}, children=act_cards)
        ])

    # ── SANCTIONS ──
    sc_col = "var(--red)" if sc_count > 0 else "var(--green)"
    sanctions_section = section("SANCTIONS & PEP CHECK", [
        html.Div(style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"10px","marginBottom":"16px"}, children=[
            html.Div(style={"backgroundColor":"var(--bg)","border":"1px solid var(--border)","borderRadius":"5px","padding":"14px","textAlign":"center"}, children=[
                html.Div(lbl, style={"color":"var(--text3)","fontSize":"9px","letterSpacing":"2px","marginBottom":"6px"}),
                html.Div(val, style={"color":col,"fontSize":"11px","fontWeight":"500"}),
            ]) for lbl,val,col in [
                ("OFAC", ai.get("sanctions",{}).get("ofac","—"), "var(--text2)"),
                ("UNION EUROPÉENNE", ai.get("sanctions",{}).get("ue","—"), "var(--text2)"),
                ("NATIONS UNIES", ai.get("sanctions",{}).get("onu","—"), "var(--text2)"),
                ("OPENSANCTIONS", f"{sc_count} hit(s)", sc_col),
            ]
        ]),
        *([html.Div(style={"backgroundColor":"rgba(255,68,85,0.06)","borderLeft":"3px solid var(--red)","padding":"12px 16px","marginBottom":"8px","borderRadius":"3px"}, children=[
            html.Div(f"⚠  {h.get('caption','')}", style={"color":"#ff8899","fontSize":"13px","fontWeight":"500","marginBottom":"3px"}),
            html.Div(", ".join(h.get("datasets",[]))[:100], style={"color":"var(--text3)","fontSize":"10px"}),
        ]) for h in sc_hits] if sc_hits else [html.Div("✓  Société non listée dans les bases de données de sanctions (OFAC · ONU · UE · +100 listes)", style={"color":"var(--green)","fontSize":"12px"})]),
        *([html.Div(style={"marginTop":"14px","paddingTop":"14px","borderTop":"1px solid var(--border)"}, children=[
            html.Div(f"PERSONNES LIÉES : {pe_count} résultat(s)", style={"color":"var(--red)","fontSize":"10px","letterSpacing":"2px","marginBottom":"8px"}),
            *[html.Div(style={"display":"flex","justifyContent":"space-between","padding":"5px 0","borderBottom":"1px solid var(--border)"}, children=[
                html.Div(h.get("caption",""), style={"color":"var(--text)","fontSize":"12px"}),
                html.Span(", ".join(h.get("properties",{}).get("topics",[])), className="tag tag-red"),
            ]) for h in pe_hits]
        ])] if pe_count > 0 else []),
    ], accent=sc_col)

    # ── RED FLAGS ──
    flags = ai.get("red_flags",[])
    flags_section = html.Div()
    if flags:
        flag_items = []
        for i,f in enumerate(flags[:8],1):
            n = f.get("niveau","orange")
            c = "var(--red)" if n=="rouge" else ("var(--orange)" if n=="orange" else "var(--green)")
            bg = "rgba(255,68,85,0.05)" if n=="rouge" else ("rgba(255,140,0,0.05)" if n=="orange" else "rgba(0,204,102,0.05)")
            flag_items.append(html.Div(style={"background":bg,"borderLeft":f"3px solid {c}","padding":"12px 16px","marginBottom":"8px","borderRadius":"3px"}, children=[
                html.Div(style={"display":"flex","justifyContent":"space-between","marginBottom":"3px"}, children=[
                    html.Div(f"RF#{i}  —  {f.get('titre','')}", style={"color":c,"fontSize":"11px","fontWeight":"500","letterSpacing":"0.5px"}),
                    html.Span(n.upper(), className=f"tag {'tag-red' if n=='rouge' else 'tag-orange' if n=='orange' else 'tag-green'}"),
                ]),
                html.Div(f.get("detail",""), style={"color":"var(--text2)","fontSize":"11px","lineHeight":"1.5"}),
            ]))
        flags_section = section("RED FLAGS — SIGNAUX D'ALERTE", flag_items)

    # ── RÉPUTATION ──
    rep = ai.get("reputation",{})
    positifs = rep.get("positif",[])
    negatifs = rep.get("negatif",[]) + rep.get("controverses",[])
    rep_section = section("RÉPUTATION & CONTROVERSES", [
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px"}, children=[
            html.Div([
                html.Div("POINTS POSITIFS", style={"color":"var(--green)","fontSize":"9px","letterSpacing":"3px","marginBottom":"10px"}),
                *[html.Div(style={"display":"flex","gap":"8px","marginBottom":"6px","alignItems":"flex-start"}, children=[
                    html.Span("✓", style={"color":"var(--green)","fontSize":"12px","marginTop":"1px"}),
                    html.Span(p, style={"color":"var(--text2)","fontSize":"12px","lineHeight":"1.5"}),
                ]) for p in positifs[:5]],
            ]) if positifs else html.Div(),
            html.Div([
                html.Div("POINTS NÉGATIFS", style={"color":"var(--orange)","fontSize":"9px","letterSpacing":"3px","marginBottom":"10px"}),
                *[html.Div(style={"display":"flex","gap":"8px","marginBottom":"6px","alignItems":"flex-start"}, children=[
                    html.Span("⚠", style={"color":"var(--orange)","fontSize":"12px","marginTop":"1px"}),
                    html.Span(n, style={"color":"var(--text2)","fontSize":"12px","lineHeight":"1.5"}),
                ]) for n in negatifs[:5]],
            ]) if negatifs else html.Div(),
        ]),
    ])

    # ── VERDICT ──
    verdict_section = html.Div(style={
        "backgroundColor":"var(--bg2)","border":f"1px solid var(--border)",
        "borderLeft":f"4px solid {couleur}","borderRadius":"6px",
        "padding":"24px 28px","marginBottom":"16px",
    }, children=[
        html.Div("VERDICT FINAL", style={"color":"var(--text3)","fontSize":"9px","letterSpacing":"4px","marginBottom":"12px"}),
        html.P(ai.get("verdict",""), style={"color":"var(--text)","fontSize":"14px","lineHeight":"1.8","marginBottom":"20px","fontFamily":"var(--serif)"}),
        html.Div("RECOMMANDATIONS", style={"color":"var(--text3)","fontSize":"9px","letterSpacing":"4px","marginBottom":"12px","paddingTop":"16px","borderTop":"1px solid var(--border)"}),
        html.Div([html.Div(style={"display":"flex","gap":"10px","marginBottom":"8px","alignItems":"flex-start"}, children=[
            html.Div(f"{i:02d}", style={"color":"var(--gold)","fontSize":"11px","fontFamily":"var(--serif)","fontWeight":"600","minWidth":"24px","marginTop":"2px"}),
            html.Div(r, style={"color":"var(--text2)","fontSize":"12px","lineHeight":"1.6"}),
        ]) for i,r in enumerate(ai.get("recommandations",[])[:6], 1)]),
    ])

    return html.Div(className="fade-in", children=[
        score_section, grid, dir_section, act_section,
        sanctions_section, flags_section, rep_section, verdict_section,
    ])


if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("⚠  GROQ_API_KEY manquante !")
        print("   Tape : export GROQ_API_KEY='gsk_...'")
    print("\n⬡  INTELCORP — Company Intelligence v2")
    print("━" * 48)
    print("🌐  http://127.0.0.1:8051")
    print("━" * 48)
    app.run(debug=True, port=8051)
