#!/bin/zsh

set -euo pipefail

project_root=${0:A:h:h}
venv="$project_root/.venv-familysearch"
person_id=${1:-}
ancestor_generations=${2:-5}

if [[ ! "$person_id" =~ '^[A-Z0-9]{4}-[A-Z0-9]{3}$' ]]; then
  print -u2 "Uso: $0 ID-FAMILYSEARCH [GERACOES-DE-ANCESTRAIS]"
  print -u2 "Exemplo: $0 ABCD-123 5"
  exit 2
fi

if [[ ! "$ancestor_generations" =~ '^[1-9][0-9]*$' ]]; then
  print -u2 "O número de gerações deve ser um inteiro positivo."
  exit 2
fi

if [[ ! -x "$venv/bin/getmyancestors" ]]; then
  print -u2 "Preparando o ambiente isolado do importador..."
  python3 -m venv "$venv"
  "$venv/bin/python" -m pip install --disable-pip-version-check \
    -r "$project_root/requirements-familysearch.txt"
fi

timestamp=$(date +%Y%m%d-%H%M%S)
slug=${person_id:l}
gedcom="$project_root/data/familysearch-${slug}-${timestamp}.ged"
report="$project_root/reports/familysearch-${slug}-${timestamp}.json"

mkdir -p "$project_root/data" "$project_root/reports"

print "Importação local e somente leitura."
print "A senha será solicitada sem aparecer na tela e não será salva."
print "Baixando $ancestor_generations gerações de ancestrais diretos, com cônjuges e casamentos."

"$venv/bin/getmyancestors" \
  --individuals "$person_id" \
  --ascend "$ancestor_generations" \
  --descend 0 \
  --marriage \
  --rate-limit 2 \
  --outfile "$gedcom"

root_xref=$(awk -v fsid="$person_id" '
  $1 == "0" && $3 == "INDI" { current = $2 }
  $1 == "1" && $2 == "_FSFTID" && $3 == fsid { print current; exit }
' "$gedcom")

if [[ -z "$root_xref" ]]; then
  print -u2 "GEDCOM criado, mas não foi possível localizar a pessoa inicial para priorização."
  print -u2 "Arquivo: $gedcom"
  exit 3
fi

cd "$project_root"
python3 -m mygenealogy.cli "$gedcom" --root "$root_xref" --output "$report" || validation_status=$?

print
print "GEDCOM privado: $gedcom"
print "Relatório de validação: $report"
if (( ${validation_status:-0} == 1 )); then
  print "A validação encontrou problemas críticos; isso é esperado nesta fase investigativa."
fi
