#!/bin/sh
# build_app.sh – baut „Steckwerk Desktop.app“ und das ZIP für den Mac (nur auf macOS).
#
#   ./build_app.sh            → ../dist/Steckwerk Desktop.app + ../dist/Steckwerk-Desktop-<version>-macOS.zip
#   ./build_app.sh /tmp/out   anderer Zielordner
#
# Die App enthält das Swift-Programm und die Python-Engine (dieselben Dateien wie die Browser-App,
# Liste aus packaging/build_macos.py) plus bridge_start.py. Python kommt vom Mac.
set -eu

VERSION="0.1.0"
HERE="$(cd "$(dirname "$0")" && pwd -P)"
ROOT="$(cd "$HERE/../.." && pwd -P)"
OUT="${1:-$HERE/../dist}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd -P)"
APP="$OUT/Steckwerk Desktop.app"
ENGINE_VERSION="$(cd "$ROOT" && python3 -c 'import steckwerk; print(steckwerk.__version__)')"

cd "$HERE"
if swift build -c release --arch arm64 --arch x86_64 >/dev/null 2>&1; then
  BIN="$(swift build -c release --arch arm64 --arch x86_64 --show-bin-path)/SteckwerkDesktop"
else
  swift build -c release
  BIN="$(swift build -c release --show-bin-path)/SteckwerkDesktop"
fi

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/steckwerk"
cp "$BIN" "$APP/Contents/MacOS/SteckwerkDesktop"
cp "$ROOT/packaging/macos/Steckwerk.icns" "$APP/Contents/Resources/AppIcon.icns"

# Engine-Dateien
(cd "$ROOT" && python3 -c 'import sys; sys.path.insert(0, "packaging"); import build_macos; print("\n".join(build_macos.code_files()))') |
while IFS= read -r f; do
  mkdir -p "$APP/Contents/Resources/steckwerk/$(dirname "$f")"
  cp "$ROOT/$f" "$APP/Contents/Resources/steckwerk/$f"
done
cp "$HERE/bridge_start.py" "$APP/Contents/Resources/steckwerk/bridge_start.py"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Steckwerk Desktop</string>
  <key>CFBundleDisplayName</key><string>Steckwerk Desktop</string>
  <key>CFBundleIdentifier</key><string>de.steckwerk.desktop</string>
  <key>CFBundleExecutable</key><string>SteckwerkDesktop</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>CFBundleVersion</key><string>$VERSION</string>
  <key>SteckwerkEngineVersion</key><string>$ENGINE_VERSION</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>CFBundleDevelopmentRegion</key><string>de</string>
  <key>LSApplicationCategoryType</key><string>public.app-category.graphics-design</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSHumanReadableCopyright</key><string>Steckwerk – parametrische, validierte Lasercut-SVGs</string>
</dict>
</plist>
PLIST

# Ad-hoc signieren (Apple Silicon startet sonst nichts); ohne Developer-ID bleibt die App „unsigniert“.
codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || echo "Hinweis: codesign nicht möglich"

ZIP="$OUT/Steckwerk-Desktop-$VERSION-macOS.zip"
rm -f "$ZIP"
(cd "$OUT" && ditto -c -k --keepParent "Steckwerk Desktop.app" "$ZIP")
echo "Fertig: $APP"
echo "ZIP:    $ZIP"
