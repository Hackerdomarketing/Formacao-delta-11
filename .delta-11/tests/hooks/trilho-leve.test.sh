#!/usr/bin/env bash
# Teste do vigia trilho-leve.py (v6.4.1): merge de [AJUSTE] so passa se a branch muda SO arquivos visuais.
source "$(dirname "$0")/_ajudante-hooks-python.sh" trilho-leve
checagens_basicas

novo_projeto
mkdir -p extension/css extension/js
echo "a { color: red; }" > extension/css/style.css
echo "console.log(1)" > extension/js/app.js
echo "<div>oi</div>" > extension/newtab.html
git init -q && git config user.email t@t && git config user.name t && git add -A && git commit -qm inicio
ramo() {  # ramo NOME ARQUIVO CONTEUDO-ACRESCENTADO
    git checkout -q -b "$1" main 2>/dev/null || git checkout -q -b "$1" master
    printf '%s\n' "$3" >> "$2"; git add -A && git commit -qm "$1"; git checkout -q - 
}
BASE_BRANCH=$(git branch --show-current)
ramo so-css extension/css/style.css ".coluna { width: 280px; }"
ramo com-js extension/js/app.js "console.log(2)"
ramo html-limpo extension/newtab.html "<span class=\"etiqueta\">x</span>"
ramo html-script extension/newtab.html "<script>alert(1)</script>"
ramo html-onclick extension/newtab.html "<button onclick=\"x()\">b</button>"
git checkout -q "$BASE_BRANCH"
merge() { evento tool_name=Bash "tool_input.command=git merge --no-ff $1 -m \"$2\""; }

espera 0 "merge [AJUSTE] so de CSS: passa" "$(merge so-css '[AJUSTE] T-271 colunas iguais')"
log_contem "trilho-leve.*VISUAL-OK T-271"
espera 2 "merge [AJUSTE] que muda JavaScript: bloqueia (volta ao trilho completo)" "$(merge com-js '[AJUSTE] T-272 dica')"
stderr_contem "extension/js/app.js"
stderr_contem "TRILHO COMPLETO"
espera 0 "HTML sem script: conta como visual" "$(merge html-limpo '[AJUSTE] T-273 etiqueta')"
espera 2 "HTML com <script> novo: bloqueia" "$(merge html-script '[AJUSTE] T-274 x')"
espera 2 "HTML com onclick novo: bloqueia" "$(merge html-onclick '[AJUSTE] T-275 x')"
espera 0 "merge SEM [AJUSTE] na mensagem: nao e com este vigia" "$(merge com-js 'T-276 logica nova')"
espera 2 "[AJUSTE] com branch que nao existe: bloqueia" "$(merge nao-existe '[AJUSTE] T-277 x')"
espera 0 "merge dentro de comando composto (cd && git merge): reconhece" "$(evento tool_name=Bash "tool_input.command=cd $TEST_DIR && git merge --no-ff so-css -m '[AJUSTE] T-278 x'")"
log_contem "VISUAL-OK T-278"
espera 0 "outra ferramenta: passa" "$(evento tool_name=Edit tool_input.file_path=extension/js/app.js)"
fim
