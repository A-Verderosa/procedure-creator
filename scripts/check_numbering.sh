#!/usr/bin/env bash
# Vérification rapide de la numérotation des sections dans un template ou rendu.md
# Usage: bash check_numbering.sh <fichier.md>

echo "=== Sections numérotées ==="
grep -nE '^## [0-9]+\.' "$1" | while IFS=: read -r line num_rest; do
    num=$(echo "$num_rest" | grep -oE '^[0-9]+')
    echo "  Ligne $line → Section $num"
done

echo ""
echo "=== Sections non numérotées ==="
grep -nE '^## [^0-9]' "$1" | grep -v '^## 🔗'
