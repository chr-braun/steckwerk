import Foundation

public struct BridgeError: LocalizedError, Sendable {
    public var message: String
    public init(_ message: String) { self.message = message }
    public var errorDescription: String? { message }
}

/// HTTP-Verbindung zur lokalen Engine (webui.py). Jeder POST trägt den Header `X-Steckwerk`,
/// sonst lehnt die Engine ab (Schutz gegen fremde Webseiten).
public final class Bridge: @unchecked Sendable {
    public let baseURL: URL
    public let client: String
    private let session: URLSession

    public init(port: Int, client: String = "desktop-" + String(UUID().uuidString.prefix(8)),
                session: URLSession? = nil) {
        self.baseURL = URL(string: "http://127.0.0.1:\(port)")!
        self.client = client
        if let session {
            self.session = session
        } else {
            let cfg = URLSessionConfiguration.ephemeral
            cfg.timeoutIntervalForRequest = 330       // Bildmodelle brauchen bis zu 5 Minuten
            cfg.connectionProxyDictionary = [:]       // nie über einen Proxy zu 127.0.0.1
            self.session = URLSession(configuration: cfg)
        }
    }

    public func url(_ path: String, lang: String = "de") -> URL {
        var comps = URLComponents(url: baseURL, resolvingAgainstBaseURL: false)!
        comps.path = path.hasPrefix("/") ? path : "/" + path
        if lang != "de" { comps.queryItems = [URLQueryItem(name: "lang", value: lang)] }
        return comps.url!
    }

    public func getRequest(_ path: String) -> URLRequest {
        var r = URLRequest(url: url(path))
        r.httpMethod = "GET"
        r.setValue("application/json", forHTTPHeaderField: "Accept")
        return r
    }

    public func postRequest(_ path: String, body: [String: JSONValue] = [:], timeout: TimeInterval = 60) throws -> URLRequest {
        var r = URLRequest(url: url(path))
        r.httpMethod = "POST"
        r.timeoutInterval = timeout
        r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        r.setValue("1", forHTTPHeaderField: "X-Steckwerk")
        var b = body
        if b["client"] == nil { b["client"] = .string(client) }
        r.httpBody = try JSONEncoder().encode(b)
        return r
    }

    // MARK: - Aufrufe

    public func data(for request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, http.statusCode >= 400 {
            if let msg = try? JSONDecoder().decode(JSONValue.self, from: data)["error"]?.stringValue {
                throw BridgeError(msg)
            }
            throw BridgeError("Engine meldet Fehler \(http.statusCode)")
        }
        return data
    }

    public func post<T: Decodable>(_ path: String, _ body: [String: JSONValue] = [:], as type: T.Type,
                                   timeout: TimeInterval = 60) async throws -> T {
        let d = try await data(for: try postRequest(path, body: body, timeout: timeout))
        return try JSONDecoder().decode(T.self, from: d)
    }

    /// POST mit loser Antwort; `ok: false` wird zum Fehler mit dem deutschen Text der Engine.
    @discardableResult
    public func call(_ path: String, _ body: [String: JSONValue] = [:], timeout: TimeInterval = 60) async throws -> JSONValue {
        let v = try await post(path, body, as: JSONValue.self, timeout: timeout)
        if v["ok"]?.boolValue == false {
            throw BridgeError(v["error"]?.stringValue ?? "Unbekannter Fehler")
        }
        return v
    }

    public func ping() async -> PingInfo? {
        guard let r = try? postRequest("/api/ping", timeout: 2),
              let d = try? await data(for: r),
              let info = try? JSONDecoder().decode(PingInfo.self, from: d),
              info.app == "steckwerk" else { return nil }
        return info
    }

    public func bye() async {
        _ = try? await data(for: try postRequest("/api/bye", timeout: 2))
    }

    public func schema() async throws -> Schema {
        try Schema.decode(try await data(for: getRequest("/api/schema")))
    }

    public func generate(_ request: BuildRequest) async throws -> GenerateResult {
        try await post("/api/generate", request.body, as: GenerateResult.self, timeout: 180)
    }

    /// ZIP mit SVGs und Prüfberichten (nur wenn alles CUT-READY ist).
    public func zip(_ request: BuildRequest) async throws -> Data {
        try await data(for: try postRequest("/api/zip", body: request.body, timeout: 180))
    }
}

public struct PingInfo: Decodable, Sendable {
    public var ok: Bool
    public var app: String
    public var version: String
    public var pid: Int?

    enum CodingKeys: String, CodingKey { case ok, app, version, pid }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        app = try c.decodeIfPresent(String.self, forKey: .app) ?? ""
        version = try c.decodeIfPresent(String.self, forKey: .version) ?? ""
        pid = try c.decodeIfPresent(Int.self, forKey: .pid)
    }
}

/// Anfrage {model, params, config} für /api/generate, /api/zip und /api/save.
public struct BuildRequest: Sendable, Hashable {
    public var model: String
    public var params: [String: JSONValue]
    public var config: [String: JSONValue]

    public init(model: String, params: [String: JSONValue], config: [String: JSONValue]) {
        self.model = model
        self.params = params
        self.config = config
    }

    public var body: [String: JSONValue] {
        ["model": .string(model), "params": .object(params), "config": .object(config)]
    }
}

/// Ausgabe der Engine auf stdout: „STECKWERK_PORT=12345“ meldet den gewählten Port.
public enum EnginePort {
    public static func parse(_ line: String) -> Int? {
        guard let r = line.range(of: "STECKWERK_PORT=") else { return nil }
        let digits = line[r.upperBound...].prefix { $0.isNumber }
        guard let p = Int(digits), (1...65535).contains(p) else { return nil }
        return p
    }
}
