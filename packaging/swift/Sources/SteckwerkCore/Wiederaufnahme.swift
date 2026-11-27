import Foundation

/// Was die App vor einem Selbst-Neustart (App-Update) sichert und danach wiederherstellt:
/// die geöffnete Ansicht, die Werte der Vorlagen, das offene Projekt und das gewählte Blatt.
///
/// Wird nur einmal gelesen (`nehmen` löscht den Eintrag) und gilt nur kurz – ein normaler Start später
/// beginnt wie gewohnt.
public struct Wiederaufnahme: Codable, Equatable, Sendable {
    public static let defaultsKey = "wiederaufnahme"
    /// Wie lange nach dem Sichern der Zustand noch übernommen wird.
    public static let gueltigkeit: TimeInterval = 10 * 60

    /// „alle“, „bereich:<id>“, „model:<id>“, „pakete“, „ki“, „material“ oder „updates“.
    public var auswahl: String?
    public var werte: [String: [String: JSONValue]]
    public var projekt: String?
    public var projektGeaendert: Bool
    public var blatt: Int
    public var gesichert: Date

    public init(auswahl: String?, werte: [String: [String: JSONValue]], projekt: String? = nil,
                projektGeaendert: Bool = false, blatt: Int = 0, gesichert: Date = Date()) {
        self.auswahl = auswahl
        self.werte = werte
        self.projekt = projekt
        self.projektGeaendert = projektGeaendert
        self.blatt = blatt
        self.gesichert = gesichert
    }

    public func sichern(in defaults: UserDefaults = .standard) {
        if let data = try? JSONEncoder().encode(self) {
            defaults.set(data, forKey: Self.defaultsKey)
        }
    }

    /// Liest den gesicherten Zustand und löscht ihn; nil, wenn keiner da oder er zu alt ist.
    public static func nehmen(aus defaults: UserDefaults = .standard, jetzt: Date = Date()) -> Wiederaufnahme? {
        guard let data = defaults.data(forKey: defaultsKey) else { return nil }
        defaults.removeObject(forKey: defaultsKey)
        guard let w = try? JSONDecoder().decode(Wiederaufnahme.self, from: data) else { return nil }
        let alter = jetzt.timeIntervalSince(w.gesichert)
        return alter >= 0 && alter <= gueltigkeit ? w : nil
    }
}
