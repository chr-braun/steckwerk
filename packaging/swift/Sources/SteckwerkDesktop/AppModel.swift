import AppKit
import SteckwerkCore
import SwiftUI

enum EngineState: Equatable {
    case starting
    case running
    case failed
}

enum SidebarItem: Hashable {
    case model(String)
    case pakete
    case ki
    case material
    case updates
}

struct AppAlert: Identifiable {
    let id = UUID()
    let title: String
    let message: String
}

/// Zustand der App. Projektlogik bleibt in der Python-Engine; hier wird nur gesteuert und angezeigt.
@MainActor
final class AppModel: ObservableObject {
    @Published private(set) var engineState: EngineState = .starting
    @Published private(set) var engineError: String?
    @Published private(set) var engineDetails = ""
    @Published private(set) var engineVersion: String?
    @Published private(set) var schema: Schema?
    @Published var selection: SidebarItem? {
        didSet { if selectedModelID != nil { schedulePreview() } }
    }
    @Published private(set) var values: [String: [String: JSONValue]] = [:]
    @Published private(set) var material: [String: JSONValue] = [:]
    @Published private(set) var result: GenerateResponse?
    @Published private(set) var resultModelID: String?
    @Published private(set) var resultIsStale = false
    @Published private(set) var geometry: [SheetGeometry] = []
    @Published var selectedSheet = 0
    @Published private(set) var isBuilding = false
    @Published private(set) var isPreviewing = false
    @Published var statusMessage: String?
    @Published var alert: AppAlert?
    /// Ergebnis der letzten Update-Prüfung (beim Start oder unter „Updates“): Pakete und die App selbst.
    @Published var updateCheck: UpdateCheck?
    @Published var desktopCheck: DesktopCheck?

    private(set) var client: EngineClient?
    private var engine: EngineProcess?
    private var pingTask: Task<Void, Never>?
    private var previewTask: Task<Void, Never>?
    private var buildSerial = 0
    private static let materialDefaultsKey = "material"
    static let autoUpdateKey = "updatesBeimStart"

    nonisolated static var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "Entwicklung"
    }

    init() {
        if let data = UserDefaults.standard.data(forKey: Self.materialDefaultsKey),
           let saved = try? JSONDecoder().decode([String: JSONValue].self, from: data) {
            material = saved
        }
    }

    // MARK: Engine

    var selectedModelID: String? {
        if case .model(let id) = selection { return id }
        return nil
    }

    var canExport: Bool {
        guard let result, !resultIsStale, resultModelID == selectedModelID else { return false }
        return result.canExport
    }

    func startEngine() async {
        guard engine == nil || engineState == .failed else { return }
        engineState = .starting
        engineError = nil
        engineDetails = ""
        let env = ProcessInfo.processInfo.environment
        guard let root = EngineLocator.engineRoot(environment: env, resourceURL: Bundle.main.resourceURL),
              let script = EngineLocator.bridgeScript(engineRoot: root) else {
            fail(EngineLaunchError.engineNotFound)
            return
        }
        let home = NSHomeDirectory()
        let python = await Task.detached { EngineLocator.findPython(environment: env, home: home) }.value
        guard let python else {
            fail(EngineLaunchError.pythonNotFound)
            return
        }
        let process = EngineProcess(python: python, script: script, engineRoot: root, environment: env)
        engine = process
        do {
            let start = try await process.start()
            let client = EngineClient(port: start.port)
            let ping = try await client.ping(timeout: 5)
            self.client = client
            engineVersion = ping.version
            try await loadSchema()
            engineState = .running
            startPinging()
            if UserDefaults.standard.object(forKey: Self.autoUpdateKey) as? Bool ?? true {
                Task { await checkForUpdates(quiet: true) }
            }
        } catch {
            fail(error)
            Task.detached { process.stop(grace: 0.2) }
        }
    }

    func restartEngine() {
        let old = engine
        engine = nil
        client = nil
        pingTask?.cancel()
        Task {
            await Task.detached { old?.stop() }.value
            await startEngine()
        }
    }

    /// Beim Beenden der App: abmelden und eigenen Kindprozess sicher beenden.
    func shutdown() {
        pingTask?.cancel()
        if let client {
            let done = DispatchSemaphore(value: 0)
            Task.detached {
                try? await client.bye()
                done.signal()
            }
            _ = done.wait(timeout: .now() + 1.5)
        }
        engine?.stop()
        engine = nil
        client = nil
    }

    private func fail(_ error: Error) {
        engineState = .failed
        engineError = error.localizedDescription
        if let launch = error as? EngineLaunchError {
            engineDetails = launch.details
        } else if let engine {
            engineDetails = engine.stderrTail
        }
    }

    private func startPinging() {
        pingTask?.cancel()
        pingTask = Task { [weak self] in
            var misses = 0
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 30_000_000_000)
                guard let self, let client = self.client, !Task.isCancelled else { return }
                do {
                    _ = try await client.ping()
                    misses = 0
                } catch {
                    misses += 1
                    if misses >= 2 {
                        self.fail(EngineLaunchError.startFailed(details: self.engine?.stderrTail ?? ""))
                        self.engineError = "Die Engine antwortet nicht mehr."
                        return
                    }
                }
            }
        }
    }

    // MARK: Updates

    /// Pfad der laufenden App, wenn sie als „Steckwerk Desktop.app“ läuft (sonst nil, z. B. bei `swift run`).
    nonisolated static var bundlePath: String? {
        let url = Bundle.main.bundleURL
        return url.pathExtension == "app" ? url.path : nil
    }

    /// Anzahl der Updates für das Abzeichen in der Seitenleiste.
    var updateCount: Int {
        let pakete = updateCheck?.pakete.filter { $0.installiert != nil && $0.installable }.count ?? 0
        return pakete + (desktopCheck?.neu == true ? 1 : 0)
    }

    func checkForUpdates(quiet: Bool = false) async {
        guard let client else { return }
        do {
            async let pakete = client.updateCheck()
            async let app = client.desktopCheck(bundle: Self.bundlePath)
            (updateCheck, desktopCheck) = try await (pakete, app)
        } catch {
            if !quiet { show(error, title: "Update-Prüfung fehlgeschlagen") }
        }
    }

    /// Neue Version laden, die App an ihrem Ort ersetzen und neu starten.
    func installDesktopUpdate() async throws -> String {
        guard let client else { throw EngineError.notRunning }
        guard let bundle = Self.bundlePath else {
            throw EngineError.server("Steckwerk Desktop läuft nicht als App – bitte von Hand aktualisieren.")
        }
        let done = try await client.desktopInstallieren(bundle: bundle)
        relaunch(at: done.pfad)
        return done.message ?? "Steckwerk Desktop \(done.version) ist installiert"
    }

    /// Startet die App am Pfad neu, sobald dieser Prozess beendet ist, und beendet sich dann.
    private func relaunch(at path: String) {
        let pid = String(ProcessInfo.processInfo.processIdentifier)
        let helper = Process()
        helper.executableURL = URL(fileURLWithPath: "/bin/sh")
        helper.arguments = ["-c", "while kill -0 \"$1\" 2>/dev/null; do sleep 0.2; done; open \"$0\"", path, pid]
        helper.standardInput = FileHandle.nullDevice
        helper.standardOutput = FileHandle.nullDevice
        helper.standardError = FileHandle.nullDevice
        do {
            try helper.run()
        } catch {
            alert = AppAlert(title: "Neustart nicht möglich",
                             message: "Die neue Version ist installiert. Bitte Steckwerk Desktop von Hand neu starten.")
            return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { NSApp.terminate(nil) }
    }

    // MARK: Schema und Werte

    func loadSchema() async throws {
        guard let client else { throw EngineError.notRunning }
        apply(schema: try await client.schema())
    }

    func reloadSchema() async {
        do {
            try await loadSchema()
        } catch {
            show(error, title: "Modelle konnten nicht geladen werden")
        }
    }

    func apply(schema: Schema) {
        self.schema = schema
        for p in schema.config where material[p.key] == nil {
            material[p.key] = p.defaultValue
        }
        if let id = selectedModelID, schema.models[id] == nil {
            selection = nil
        }
        if selection == nil {
            let preferred = schema.models["wichtelhaus"] != nil ? "wichtelhaus" : schema.sidebarGroups.first?.models.first?.id
            selection = preferred.map(SidebarItem.model)
        }
    }

    func values(for modelID: String) -> [String: JSONValue] {
        guard let info = schema?.models[modelID] else { return values[modelID] ?? [:] }
        return ParameterLogic.defaults(for: info.params).merging(values[modelID] ?? [:]) { _, new in new }
    }

    func binding(for param: Param, in modelID: String) -> Binding<JSONValue> {
        Binding(
            get: { self.values[modelID]?[param.key] ?? param.defaultValue },
            set: { newValue in
                self.values[modelID, default: [:]][param.key] = ParameterLogic.coerce(newValue, for: param)
                if self.resultModelID == modelID { self.resultIsStale = true }
                self.schedulePreview()
            }
        )
    }

    func materialBinding(for param: Param) -> Binding<JSONValue> {
        Binding(
            get: { self.material[param.key] ?? param.defaultValue },
            set: { newValue in
                self.material[param.key] = ParameterLogic.coerce(newValue, for: param)
                self.resultIsStale = true
                self.schedulePreview()
                if let data = try? JSONEncoder().encode(self.material) {
                    UserDefaults.standard.set(data, forKey: Self.materialDefaultsKey)
                }
            }
        )
    }

    func resetValues(for modelID: String) {
        values[modelID] = nil
        if resultModelID == modelID { resultIsStale = true }
        schedulePreview()
    }

    func resetMaterial() {
        material = [:]
        UserDefaults.standard.removeObject(forKey: Self.materialDefaultsKey)
        if let schema { apply(schema: schema) }
        resultIsStale = true
        schedulePreview()
    }

    /// Übernimmt Werte des Assistenten; liefert die geänderten Parameter.
    func applySuggestion(_ werte: [String: JSONValue], to modelID: String) -> [String] {
        guard let info = schema?.models[modelID] else { return [] }
        var current = values(for: modelID)
        let changed = ParameterLogic.apply(werte, to: &current, params: info.params)
        values[modelID] = current
        if !changed.isEmpty && resultModelID == modelID { resultIsStale = true }
        if !changed.isEmpty { schedulePreview() }
        return changed
    }

    private func requestBody(for modelID: String) -> (params: [String: JSONValue], config: [String: JSONValue])? {
        guard let schema, let info = schema.models[modelID] else { return nil }
        return (ParameterLogic.requestValues(info.params, values: values(for: modelID)),
                ParameterLogic.requestValues(schema.config, values: material))
    }

    // MARK: Bauen und Exportieren

    /// Vorschau nach kurzer Pause neu bauen, damit jede Änderung sofort im Blatt sichtbar wird.
    func schedulePreview() {
        previewTask?.cancel()
        guard engineState == .running, selectedModelID != nil else { return }
        previewTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 450_000_000)
            guard !Task.isCancelled else { return }
            await self?.build(quiet: true)
        }
    }

    /// Baut das Modell. `quiet` ist die automatische Vorschau: ohne Meldungen, ohne Sperre für den Knopf.
    func build(quiet: Bool = false) async {
        guard let client, let id = selectedModelID, let body = requestBody(for: id) else { return }
        if !quiet {
            previewTask?.cancel()
            guard !isBuilding else { return }
            isBuilding = true
            statusMessage = nil
        }
        buildSerial += 1
        let serial = buildSerial
        if quiet { isPreviewing = true }
        defer {
            if quiet {
                if serial == buildSerial { isPreviewing = false }
            } else {
                isBuilding = false
            }
        }
        do {
            let response = try await client.generate(model: id, params: body.params, config: body.config)
            guard serial == buildSerial else { return }
            let engraveColor = body.config["engrave_color"]?.stringValue ?? "#0000FF"
            let sheets = response.assemblies.flatMap(\.sheets)
            let shapes = await Task.detached {
                sheets.map { SheetGeometry.parse(svg: $0.svg, engraveColor: engraveColor) }
            }.value
            guard serial == buildSerial else { return }
            geometry = shapes
            result = response
            resultModelID = id
            resultIsStale = false
            if !quiet { selectedSheet = 0 }
        } catch {
            if Task.isCancelled || serial != buildSerial { return }
            if !quiet { show(error, title: "Bauen fehlgeschlagen") }
        }
    }

    /// Fragt nach einem Ordner und schreibt SVGs und Prüfbericht hinein (nur nach bestandener Prüfung).
    func exportToChosenFolder() async {
        if !canExport { await build() }
        guard canExport, let result else {
            alert = AppAlert(title: "Export nicht möglich",
                             message: "Exportiert wird erst, wenn der Validator alles als CUT-READY bestätigt hat.")
            return
        }
        let panel = NSOpenPanel()
        panel.title = "Ordner für den Export wählen"
        panel.prompt = "Exportieren"
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.canCreateDirectories = true
        panel.allowsMultipleSelection = false
        guard panel.runModal() == .OK, let folder = panel.url else { return }
        do {
            let written = try ReportFormatter.write(ReportFormatter.exportFiles(result), to: folder)
            statusMessage = "\(written.count) Dateien exportiert nach \(folder.lastPathComponent)"
            NSWorkspace.shared.activateFileViewerSelecting(written.isEmpty ? [folder] : [written[0]])
        } catch {
            show(error, title: "Export fehlgeschlagen")
        }
    }

    /// Speichert über die Engine in deren Ausgabeordner (Dokumente/Steckwerk).
    func saveToEngineFolder() async {
        guard let client, let id = selectedModelID, let body = requestBody(for: id) else { return }
        do {
            let saved = try await client.save(model: id, params: body.params, config: body.config)
            statusMessage = "\(saved.files.count) Dateien gespeichert"
        } catch {
            show(error, title: "Speichern fehlgeschlagen")
        }
    }

    func openFolder() async {
        guard let client else { return }
        do {
            try await client.openFolder()
        } catch {
            show(error, title: "Ordner lässt sich nicht öffnen")
        }
    }

    func show(_ error: Error, title: String) {
        alert = AppAlert(title: title, message: error.localizedDescription)
    }
}
