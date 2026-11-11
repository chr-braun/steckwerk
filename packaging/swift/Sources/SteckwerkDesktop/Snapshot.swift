import AppKit
import SteckwerkCore
import SwiftUI

/// `Steckwerk Desktop --snapshot <Ordner>`: startet die App unsichtbar für den Nutzer, baut das Wichtelhaus und
/// legt Bilder des Fensters und der Blätter (Ausgeben, Prüfbericht) hell und dunkel als PNG ab.
/// Für CI und die Doku; nutzt die Umgebung des Aufrufs (z. B. STECKWERK_HOME für Beispielprojekte).
@MainActor
enum Snapshot {
    static func runAndExit(folder: String) -> Never {
        let app = NSApplication.shared
        app.setActivationPolicy(.accessory)
        let dir = URL(fileURLWithPath: folder, isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        Task { @MainActor in
            let code = await perform(dir)
            exit(code)
        }
        app.run()
        exit(0)
    }

    private static func perform(_ dir: URL) async -> Int32 {
        let model = AppModel()
        model.showInspector = true
        let host = NSHostingController(rootView: ContentView().environmentObject(model))
        host.sceneBridgingOptions = [.all]
        host.sizingOptions = []  // sonst schrumpft das Fenster auf die Mindestgröße des Inhalts
        let window = NSWindow(contentViewController: host)
        window.styleMask = [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView]
        window.toolbarStyle = .unified
        window.setContentSize(NSSize(width: 1280, height: 800))
        window.setFrameOrigin(NSPoint(x: 40, y: 40))
        window.orderFrontRegardless()

        await model.startEngine()
        guard model.engineState == .running else {
            FileHandle.standardError.write(Data("SNAPSHOT FEHLER · Engine: \(model.engineError ?? "?")\n".utf8))
            return 1
        }
        for (name, vorlage) in [("Schwibbogen Seiffen", "schwibbogen"), ("Adventsstern groß", "ornament"),
                                ("Wichtelhaus für Lena", "wichtelhaus")] where model.schema?.models[vorlage] != nil {
            model.selection = .model(vorlage)
            await model.saveProject(named: name)
        }
        if let lena = model.projekte.first(where: { $0.name == "Wichtelhaus für Lena" }) { model.openProject(lena) }
        guard await waitForResult(model) else {
            FileHandle.standardError.write(Data("SNAPSHOT FEHLER · keine Vorschau\n".utf8))
            return 1
        }
        model.statusMessage = nil
        window.setContentSize(NSSize(width: 1280, height: 800))

        for (suffix, appearance) in [("hell", NSAppearance(named: .aqua)), ("dunkel", NSAppearance(named: .darkAqua))] {
            NSApp.appearance = appearance
            await pause(1.2)
            save(window, to: dir.appendingPathComponent("1-hauptfenster-\(suffix).png"))
            model.showExport = true
            await pause(1.5)
            if let sheet = window.attachedSheet { save(sheet, to: dir.appendingPathComponent("2-ausgeben-\(suffix).png")) }
            model.showExport = false
            await pause(1.0)
            model.showReport = true
            await pause(1.5)
            if let sheet = window.attachedSheet { save(sheet, to: dir.appendingPathComponent("3-pruefbericht-\(suffix).png")) }
            model.showReport = false
            await pause(1.0)
        }
        print("SNAPSHOT OK · \(dir.path)")
        return 0
    }

    private static func waitForResult(_ model: AppModel) async -> Bool {
        for _ in 0..<240 {
            if model.result != nil, !model.isPreviewing, !model.isBuilding, !model.resultIsStale { return true }
            await pause(0.25)
        }
        return false
    }

    private static func pause(_ seconds: Double) async {
        try? await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
    }

    /// Fenster samt Titel- und Werkzeugleiste als PNG.
    private static func save(_ window: NSWindow, to url: URL) {
        guard let view = window.contentView?.superview ?? window.contentView else { return }
        view.layoutSubtreeIfNeeded()
        guard let rep = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { return }
        view.cacheDisplay(in: view.bounds, to: rep)
        if let data = rep.representation(using: .png, properties: [:]) {
            try? data.write(to: url)
            print("SNAPSHOT · \(url.lastPathComponent) \(Int(view.bounds.width))×\(Int(view.bounds.height))")
        }
    }
}
