import AppKit
import SteckwerkCore
import SwiftUI

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    let model = AppModel()

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    func applicationWillTerminate(_ notification: Notification) {
        model.shutdown()
    }
}

@main
@MainActor
enum Launcher {
    static func main() {
        if CommandLine.arguments.contains("--self-test") {
            SelfTest.runAndExit()
        }
        if let i = CommandLine.arguments.firstIndex(of: "--snapshot"), CommandLine.arguments.count > i + 1 {
            Snapshot.runAndExit(folder: CommandLine.arguments[i + 1])
        }
        SteckwerkApp.main()
    }
}

struct SteckwerkApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var delegate

    var body: some Scene {
        Window("Steckwerk Desktop", id: "main") {
            ContentView()
                .environmentObject(delegate.model)
                .frame(minWidth: 1000, minHeight: 680)
                .task { await delegate.model.startEngine() }
        }
        .defaultSize(width: 1280, height: 820)
        .commands { AppCommands(model: delegate.model) }

        Settings {
            SettingsView()
                .environmentObject(delegate.model)
        }
    }
}

@MainActor
struct AppCommands: Commands {
    @ObservedObject var model: AppModel

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button("Ausgeben …") {
                model.showExport = true
            }
            .keyboardShortcut("e", modifiers: .command)
            .disabled(model.selectedModelID == nil || model.engineState != .running || !model.canExport)
        }

        CommandGroup(replacing: .saveItem) {
            Button("Projekt sichern") {
                model.saveCurrent()
            }
            .keyboardShortcut("s", modifiers: .command)
            .disabled(model.selectedModelID == nil || model.engineState != .running)

            Button("Als neues Projekt sichern …") {
                model.showSaveProject = true
            }
            .keyboardShortcut("s", modifiers: [.command, .shift])
            .disabled(model.selectedModelID == nil || model.engineState != .running)

            Divider()

            Button("Ordner öffnen") {
                Task { await model.openFolder() }
            }
            .keyboardShortcut("o", modifiers: .command)
            .disabled(model.engineState != .running)
        }

        CommandGroup(after: .sidebar) {
            Button(model.showInspector ? "Inspektor ausblenden" : "Inspektor einblenden") {
                model.showInspector.toggle()
            }
            .keyboardShortcut("i", modifiers: [.command, .option])
        }

        CommandMenu("Vorlage") {
            Button("Prüfbericht") {
                model.showReport = true
            }
            .keyboardShortcut("r", modifiers: .command)
            .disabled(model.result == nil)

            Button("Neu prüfen") {
                Task { await model.build() }
            }
            .keyboardShortcut("b", modifiers: .command)
            .disabled(model.selectedModelID == nil || model.engineState != .running || model.isBuilding)

            Button("Auf Standardwerte zurücksetzen") {
                if let id = model.selectedModelID { model.resetValues(for: id) }
            }
            .disabled(model.selectedModelID == nil)

            Button("Überrasch mich") {
                if let id = model.selectedModelID { model.surprise(for: id) }
            }
            .disabled(model.selectedModelID.map { !model.hasSurprise(for: $0) } ?? true)

            Divider()

            Button("Engine neu starten") {
                model.restartEngine()
            }
        }

        CommandGroup(replacing: .help) {
            Button("Steckwerk Desktop – Hilfe") {
                model.alert = AppAlert(
                    title: "Steckwerk Desktop \(AppModel.appVersion)",
                    message: "Links eine Vorlage wählen und rechts im Inspektor die Werte einstellen – die Platte wird sofort "
                        + "neu gerechnet und geprüft. Unten steht, ob sie schnittfertig ist (Klick öffnet den Prüfbericht). "
                        + "„An xTool senden“ (⌘E) öffnet sie in xTool Creative Space oder sichert die Dateien, ⌘S merkt "
                        + "sie dir als Projekt. Material und KI-Anbieter stellst du unter Einstellungen (⌘,) ein."
                )
            }
        }
    }
}
