import AppKit
import Observation
import SteckwerkCore
import SwiftUI

/// Was in der Seitenleiste gewählt ist.
enum SidebarItem: Hashable {
    case modell(String)
    case pakete
    case ki
    case material
    case updates
}

/// Zustand der App: Engine, Schema, Formularwerte und letztes Ergebnis.
@MainActor
@Observable
final class AppModel {
    var engineState: Engine.State = .gestoppt
    var schema: Schema?
    var selection: SidebarItem?
    var values: [String: [String: JSONValue]] = [:]      // je Modell
    var config: [String: JSONValue] = [:]
    var result: GenerateResult?
    var resultKey: BuildRequest?
    var busy = false
    var message: String?
    var errorText: String?
    var engineDetails: String?
    var suche = ""

    let engine = Engine()
    private(set) var bridge: Bridge?
    private var pingTask: Task<Void, Never>?
    private var autoTask: Task<Void, Never>?

    static let outDirKey = "ausgabeOrdner"
    static let configKey = "material"

    var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "dev"
    }

    var outDir: String {
        UserDefaults.standard.string(forKey: Self.outDirKey)
            ?? (NSHomeDirectory() as NSString).appendingPathComponent("Steckwerk")
    }

    var selectedModelKey: String? {
        if case .modell(let k) = selection { return k }
        return nil
    }

    var selectedModel: ModelInfo? {
        selectedModelKey.flatMap { schema?.models[$0] }
    }

    // MARK: - Engine

    func startEngine() async {
        if case .laedt = engineState { return }
        if case .laeuft = engineState { return }
        engineState = .laedt
        engineDetails = nil
        do {
            let b: Bridge
            if let found = await Engine.existing() {
                b = found.0
                engineState = .laeuft(port: Engine.defaultPort, version: found.1.version, eigen: false)
            } else {
                let started = try await engine.start(outDir: outDir)
                b = started.0
                engineState = .laeuft(port: b.baseURL.port ?? 0, version: started.1.version, eigen: true)
            }
            bridge = b
            startPinging()
            try await reloadSchema()
        } catch {
            engineState = .fehler(error.localizedDescription)
            engineDetails = error.localizedDescription
        }
    }

    func restartEngine() async {
        pingTask?.cancel()
        engine.stop()
        bridge = nil
        engineState = .gestoppt
        await startEngine()
    }

    /// Lebenszeichen, damit eine mitbenutzte Browser-App die Engine nicht beendet.
    private func startPinging() {
        pingTask?.cancel()
        pingTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 20_000_000_000)
                guard let self, let b = self.bridge else { return }
                if await b.ping() == nil {
                    if case .laeuft(_, _, let eigen) = self.engineState, eigen {
                        self.engineState = .fehler("Engine antwortet nicht mehr")
                        self.engineDetails = self.engine.lastError
                    }
                }
            }
        }
    }

    func shutdown() {
        pingTask?.cancel()
        if let b = bridge {
            let sem = DispatchSemaphore(value: 0)
            Task.detached { await b.bye(); sem.signal() }
            _ = sem.wait(timeout: .now() + 1)
        }
        engine.stopAndWait()
    }

    func reloadSchema() async throws {
        guard let b = bridge else { return }
        let s = try await b.schema()
        apply(schema: s)
    }

    func apply(schema s: Schema) {
        schema = s
        if config.isEmpty {
            var c = Dictionary(s.config.map { ($0.key, $0.defaultValue) }, uniquingKeysWith: { a, _ in a })
            if let saved = UserDefaults.standard.data(forKey: Self.configKey),
               let stored = try? JSONDecoder().decode([String: JSONValue].self, from: saved) {
                for (k, v) in stored where c[k] != nil { c[k] = v }
            }
            config = c
        }
        if selection == nil, let first = s.orderedGroups.first.flatMap({ s.models(in: $0).first }) {
            select(.modell(first.key))
        } else if let k = selectedModelKey, s.models[k] == nil {
            selection = nil
        }
    }

    func saveConfig() {
        if let d = try? JSONEncoder().encode(config) {
            UserDefaults.standard.set(d, forKey: Self.configKey)
        }
        scheduleBuild()
    }

    // MARK: - Formular

    func select(_ item: SidebarItem) {
        selection = item
        if case .modell(let k) = item, values[k] == nil, let m = schema?.models[k] {
            values[k] = m.defaults
        }
        if case .modell = item { scheduleBuild(delay: 0) }
    }

    func value(_ p: Param) -> JSONValue {
        guard let k = selectedModelKey else { return p.defaultValue }
        return values[k]?[p.key] ?? p.defaultValue
    }

    func set(_ p: Param, _ v: JSONValue) {
        guard let k = selectedModelKey else { return }
        values[k, default: [:]][p.key] = p.clamp(v)
        scheduleBuild()
    }

    func resetModel() {
        guard let k = selectedModelKey, let m = selectedModel else { return }
        values[k] = m.defaults
        scheduleBuild(delay: 0)
    }

    func currentRequest() -> BuildRequest? {
        guard let k = selectedModelKey else { return nil }
        return BuildRequest(model: k, params: values[k] ?? [:], config: config)
    }

    // MARK: - Bauen

    /// Nach einer Änderung kurz warten, dann neu bauen und prüfen (wie „live“ in der Weboberfläche).
    func scheduleBuild(delay: Double = 0.5) {
        autoTask?.cancel()
        autoTask = Task { [weak self] in
            if delay > 0 { try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000)) }
            guard !Task.isCancelled else { return }
            await self?.build()
        }
    }

    func build() async {
        guard let b = bridge, let req = currentRequest() else { return }
        busy = true
        defer { busy = false }
        do {
            let r = try await b.generate(req)
            guard req == currentRequest() else { return }     // inzwischen geändert
            result = r
            resultKey = req
            errorText = nil
        } catch {
            errorText = error.localizedDescription
        }
    }

    var canExport: Bool {
        result?.ok == true && resultKey == currentRequest()
    }

    // MARK: - Export

    /// Ordner wählen, ZIP von der Engine holen und mit `ditto` entpacken – gleiche Dateien wie im Web.
    func exportWithPanel() {
        guard canExport, let req = currentRequest(), let b = bridge else {
            errorText = "Exportieren geht erst, wenn die Prüfung „0 FEHLER“ meldet."
            return
        }
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.canCreateDirectories = true
        panel.prompt = "Hier speichern"
        panel.message = "Ordner für SVG-Dateien und Prüfbericht"
        panel.directoryURL = URL(fileURLWithPath: outDir)
        guard panel.runModal() == .OK, let dir = panel.url else { return }
        UserDefaults.standard.set(dir.path, forKey: Self.outDirKey)
        Task {
            busy = true
            defer { busy = false }
            do {
                let zip = try await b.zip(req)
                try Exporter.unzip(zip, into: dir)
                message = "Gespeichert in \(dir.path)"
                NSWorkspace.shared.activateFileViewerSelecting([dir])
            } catch {
                errorText = "Export fehlgeschlagen: \(error.localizedDescription)"
            }
        }
    }

    func openOutFolder() {
        let url = URL(fileURLWithPath: outDir)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        NSWorkspace.shared.open(url)
    }
}

enum Exporter {
    static func unzip(_ data: Data, into dir: URL) throws {
        let tmp = FileManager.default.temporaryDirectory.appendingPathComponent("steckwerk-\(UUID().uuidString).zip")
        try data.write(to: tmp)
        defer { try? FileManager.default.removeItem(at: tmp) }
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/ditto")
        p.arguments = ["-x", "-k", tmp.path, dir.path]
        try p.run()
        p.waitUntilExit()
        if p.terminationStatus != 0 {
            throw BridgeError("ditto meldet Fehler \(p.terminationStatus)")
        }
    }
}
