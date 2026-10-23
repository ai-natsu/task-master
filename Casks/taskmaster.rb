cask "taskmaster" do
  version "2.0.0"
  sha256 "79a6b72455f25f936020515067873cf0ef2cffb15876411860d91c9f56cd3742"

  url "https://github.com/ai-natsu/task-master/releases/download/v#{version}/TaskMaster-#{version}-mac.zip"
  name "TaskMaster"
  desc "Desktop task manager with projects, subtasks, kanban and Gantt views"
  homepage "https://github.com/ai-natsu/task-master"

  depends_on arch: :arm64
  depends_on macos: :monterey

  app "TaskMaster/TaskMaster.app"

  zap trash: "~/Library/Application Support/TaskMaster"

  caveats <<~EOS
    TaskMaster is not signed or notarized, so macOS shows a warning on the first launch.
    Open System Settings > Privacy & Security and click "Open Anyway",
    or run: xattr -dr com.apple.quarantine /Applications/TaskMaster.app
  EOS
end
