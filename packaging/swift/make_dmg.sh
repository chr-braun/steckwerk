#!/bin/bash
# Packt „Steckwerk Desktop.app“ in ein DMG mit Verknüpfung auf „Programme“ zum Hineinziehen.
#
#   ./make_dmg.sh [App] [Ziel.dmg]
#     Default: ../dist/Steckwerk Desktop.app → ../dist/Steckwerk-Desktop-<Version>.dmg
#
# Nur auf macOS (hdiutil). Das DMG ist wie die App nicht notarisiert.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
APP="${1:-$HERE/../dist/Steckwerk Desktop.app}"
[ -d "$APP" ] || { echo "App nicht gefunden: $APP – erst ./build_app.sh ausführen" >&2; exit 1; }
VERSION="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP/Contents/Info.plist")"
DMG="${2:-$(dirname "$APP")/Steckwerk-Desktop-$VERSION.dmg}"
VOLUME="Steckwerk Desktop $VERSION"

STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT
ditto "$APP" "$STAGING/Steckwerk Desktop.app"
ln -s /Applications "$STAGING/Programme"

# hdiutil liefert auf ausgelasteten Maschinen gelegentlich ein kaputtes Image („corrupt image“,
# „Resource busy“) – dann bis zu dreimal neu erzeugen.
for VERSUCH in 1 2 3; do
  rm -f "$DMG"
  if hdiutil create -volname "$VOLUME" -srcfolder "$STAGING" -fs HFS+ -format UDZO -imagekey zlib-level=9 -ov "$DMG" \
     && hdiutil verify "$DMG"; then
    echo "Fertig: $DMG"
    exit 0
  fi
  echo "DMG-Versuch $VERSUCH fehlgeschlagen, neuer Anlauf …" >&2
  sleep $((VERSUCH * 5))
done
echo "DMG konnte nicht erzeugt werden" >&2
exit 1
