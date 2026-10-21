import Foundation

/// Startet und beendet die Python-Engine als Kindprozess (über bridge_start.py).
public final class Engine: @unchecked Sendable {
    public enum State: Equatable, Sendable {
        case gestoppt
        case laedt
        case laeuft(port: Int, version: String, eigen: Bool)
        case fehler(String)

        public var label: String {
            switch self {
            case .gestoppt: return "gestoppt"
            case .laedt: return "lädt …"
            case .laeuft(_, let v, _): return "läuft · \(v)"
            case .fehler: return "Fehler"
            }
        }
    }

    public struct Locations: Sendable {
        public var python: String
        public var engineDir: String
        public var starter: String
    }

    public static let defaultPort = 8765
    private var process: Process?
    private let lock = NSLock()
    private var stderrTail = Data()

    public init() {}

    /// Letzte Zeilen der Fehlerausgabe – für den Dialog „Engine startet nicht“.
    public var lastError: String {
        lock.lock(); defer { lock.unlock() }
        return String(decoding: stderrTail, as: UTF8.self)
    }

    // MARK: - Suchen

    /// Python 3.8+ in derselben Reihenfolge wie die bisherige Mac-App (Homebrew zuerst).
    public static func pythonCandidates(environment: [String: String] = ProcessInfo.processInfo.environment) -> [String] {
        var c: [String] = []
        if let p = environment["STECKWERK_PYTHON"], !p.isEmpty { c.append(p) }
        let home = environment["HOME"] ?? NSHomeDirectory()
        c += ["/opt/homebrew/bin/python3", "/usr/local/bin/python3",
              "/Library/Frameworks/Python.framework/Versions/Current/bin/python3",
              home + "/.pyenv/shims/python3", "/opt/local/bin/python3", "/usr/bin/python3"]
        return c
    }

    public static func findPython(fileManager: FileManager = .default) -> String? {
        for p in pythonCandidates() where fileManager.isExecutableFile(atPath: p) {
            if p == "/usr/bin/python3" && !fileManager.fileExists(atPath: "/Library/Developer/CommandLineTools/usr/bin/python3")
                && !fileManager.fileExists(atPath: "/Applications/Xcode.app") {
                continue    // nur ein Platzhalter, solange Apples Command Line Tools fehlen
            }
            return p
        }
        return nil
    }

    /// Ordner mit webui.py: STECKWERK_ENGINE, im App-Bundle (Resources/steckwerk) oder – beim
    /// Entwickeln mit `swift run` – die Wurzel des Repos oberhalb von packaging/swift.
    public static func engineDirCandidates(bundleResources: URL?, executable: URL?,
                                           environment: [String: String] = ProcessInfo.processInfo.environment) -> [URL] {
        var c: [URL] = []
        if let e = environment["STECKWERK_ENGINE"], !e.isEmpty { c.append(URL(fileURLWithPath: e)) }
        if let r = bundleResources { c.append(r.appendingPathComponent("steckwerk")) }
        var dir = executable?.deletingLastPathComponent()
        for _ in 0..<8 {
            guard let d = dir else { break }
            c.append(d)
            dir = d.deletingLastPathComponent()
        }
        return c
    }

    public static func locate(fileManager: FileManager = .default) -> Result<Locations, BridgeError> {
        guard let py = findPython(fileManager: fileManager) else {
            return .failure(BridgeError("Kein Python 3 gefunden. Installiere die „Command Line Tools“ von Apple "
                                        + "(Terminal: xcode-select --install) oder Python von python.org."))
        }
        let dirs = engineDirCandidates(bundleResources: Bundle.main.resourceURL, executable: Bundle.main.executableURL)
        guard let dir = dirs.first(where: { fileManager.fileExists(atPath: $0.appendingPathComponent("webui.py").path) }) else {
            return .failure(BridgeError("Die Steckwerk-Engine (webui.py) fehlt im Programm."))
        }
        var starter = dir.appendingPathComponent("bridge_start.py")
        if !fileManager.fileExists(atPath: starter.path) {
            starter = dir.appendingPathComponent("packaging/swift/bridge_start.py")
        }
        guard fileManager.fileExists(atPath: starter.path) else {
            return .failure(BridgeError("bridge_start.py fehlt neben der Engine."))
        }
        return .success(Locations(python: py, engineDir: dir.path, starter: starter.path))
    }

    /// Pfad der laufenden „Steckwerk Desktop.app“ – nur dann sind Programm-Updates möglich.
    public static func runningBundle(_ bundle: Bundle = .main) -> String? {
        let path = bundle.bundlePath
        return path.hasSuffix(".app") ? path : nil
    }

    /// Neue App kurz nach dem Beenden dieser Instanz öffnen (wie der Updater der Browser-App).
    public static func relaunch(_ appPath: String) throws {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/bin/sh")
        p.arguments = ["-c", "sleep 1.5; open \"$0\"", appPath]
        try p.run()
    }

    // MARK: - Starten / Beenden

    /// Läuft schon eine Engine (z. B. die Browser-App)? Dann wird sie mitbenutzt.
    public static func existing(port: Int = defaultPort) async -> (Bridge, PingInfo)? {
        let b = Bridge(port: port)
        if let info = await b.ping() { return (b, info) }
        return nil
    }

    /// Engine starten und auf den Port warten (höchstens `timeout` Sekunden).
    public func start(outDir: String, timeout: TimeInterval = 45) async throws -> (Bridge, PingInfo) {
        let loc: Locations
        switch Engine.locate() {
        case .success(let l): loc = l
        case .failure(let e): throw e
        }
        let p = Process()
        p.executableURL = URL(fileURLWithPath: loc.python)
        p.arguments = ["-u", loc.starter, "--engine", loc.engineDir, "--port", "0", "--out", outDir,
                       "--parent", String(ProcessInfo.processInfo.processIdentifier)]
        if let bundle = Engine.runningBundle() { p.arguments! += ["--bundle", bundle] }
        p.currentDirectoryURL = URL(fileURLWithPath: loc.engineDir)
        var env = ProcessInfo.processInfo.environment
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        p.environment = env
        let out = Pipe(), err = Pipe()
        p.standardOutput = out
        p.standardError = err

        let portBox = PortBox()
        out.fileHandleForReading.readabilityHandler = { h in
            let d = h.availableData
            if d.isEmpty { h.readabilityHandler = nil; return }
            for line in String(decoding: d, as: UTF8.self).split(separator: "\n") {
                if let port = EnginePort.parse(String(line)) { portBox.set(port) }
            }
        }
        err.fileHandleForReading.readabilityHandler = { [weak self] h in
            let d = h.availableData
            if d.isEmpty { h.readabilityHandler = nil; return }
            guard let self else { return }
            self.lock.lock()
            self.stderrTail.append(d)
            if self.stderrTail.count > 4000 { self.stderrTail = self.stderrTail.suffix(4000) }
            self.lock.unlock()
        }
        try p.run()
        lock.lock(); process = p; lock.unlock()

        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if !p.isRunning {
                throw BridgeError("Die Engine hat sich sofort beendet.\n\n" + lastError)
            }
            if let port = portBox.get() {
                let b = Bridge(port: port)
                if let info = await b.ping() { return (b, info) }
            }
            try await Task.sleep(nanoseconds: 200_000_000)
        }
        stop()
        throw BridgeError("Engine startet nicht (nach \(Int(timeout)) s keine Antwort).\n\n" + lastError)
    }

    /// SIGTERM, nach 3 Sekunden hart beenden. Ohne eigenen Prozess (mitbenutzte Engine) passiert nichts.
    public func stop() {
        lock.lock()
        let p = process
        process = nil
        lock.unlock()
        guard let p, p.isRunning else { return }
        p.terminate()
        let pid = p.processIdentifier
        DispatchQueue.global().asyncAfter(deadline: .now() + 3) {
            if p.isRunning { kill(pid, SIGKILL) }
        }
    }

    /// Synchron beenden – für applicationWillTerminate.
    public func stopAndWait(timeout: TimeInterval = 3) {
        lock.lock()
        let p = process
        process = nil
        lock.unlock()
        guard let p, p.isRunning else { return }
        p.terminate()
        let end = Date().addingTimeInterval(timeout)
        while p.isRunning && Date() < end { usleep(50_000) }
        if p.isRunning { kill(p.processIdentifier, SIGKILL) }
    }
}

private final class PortBox: @unchecked Sendable {
    private let lock = NSLock()
    private var port: Int?
    func set(_ p: Int) { lock.lock(); port = p; lock.unlock() }
    func get() -> Int? { lock.lock(); defer { lock.unlock() }; return port }
}
