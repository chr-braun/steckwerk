import AppKit
import SteckwerkCore
import SwiftUI

final class AppDelegate: NSObject, NSApplicationDelegate {
    var model: AppModel?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Ohne Bundle (swift run) erscheint sonst kein Dock-Symbol und kein Menü.
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    func applicationWillTerminate(_ notification: Notification) {
        MainActor.assumeIsolated { model?.shutdown() }
    }
}

@main
struct SteckwerkApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var delegate
    @State private var model = AppModel()

    var body: some Scene {
        WindowGroup("Steckwerk Desktop") {
            ContentView()
                .environment(model)
                .frame(minWidth: 980, minHeight: 620)
                .task {
                    delegate.model = model
                    await model.startEngine()
                }
        }
        .windowToolbarStyle(.unified)
        .commands {
            CommandGroup(replacing: .newItem) {
                Button("Exportieren …") { model.exportWithPanel() }
                    .keyboardShortcut("e")
                    .disabled(!model.canExport)
                Button("Ausgabeordner öffnen") { model.openOutFolder() }
                    .keyboardShortcut("o")
            }
            CommandMenu("Modell") {
                Button("Bauen & prüfen") { Task { await model.build() } }
                    .keyboardShortcut("b")
                    .disabled(model.selectedModelKey == nil)
                Button("Standardwerte") { model.resetModel() }
                    .disabled(model.selectedModelKey == nil)
                Divider()
                Button("Engine neu starten") { Task { await model.restartEngine() } }
            }
            CommandGroup(replacing: .help) {
                Button("Steckwerk auf GitHub") {
                    if let u = URL(string: "https://github.com/chr-braun/steckwerk") { NSWorkspace.shared.open(u) }
                }
            }
        }

        Settings {
            SettingsView()
                .environment(model)
        }
    }
}

struct SettingsView: View {
    var body: some View {
        TabView {
            MaterialView()
                .tabItem { Label("Material", systemImage: "square.stack.3d.up") }
            KIView()
                .tabItem { Label("KI-Anbieter", systemImage: "sparkles") }
            AppUpdateView()
                .tabItem { Label("Updates", systemImage: "arrow.down.circle") }
        }
        .frame(width: 560, height: 520)
    }
}
