class Margin < Formula
  desc "Comment on a PDF in a terminal pane and have Claude Code act on each comment"
  homepage "https://github.com/jborlido/margin"
  # No tagged release yet, so this is a head-only formula: `brew install --HEAD margin`.
  # At the first tag, add above `head`:
  #   url "https://github.com/jborlido/margin/archive/refs/tags/v0.1.0.tar.gz"
  #   sha256 "<sha256 of that tarball>"
  license "PolyForm-Noncommercial-1.0.0"
  head "https://github.com/jborlido/margin.git", branch: "master"

  depends_on "poppler"
  depends_on "python@3.14"
  depends_on "zellij"

  def install
    # Pure stdlib, no build step: ship the package and a launcher pinned to Homebrew's Python.
    # The launcher is a Python file on purpose: margin re-runs its own argv[0] in the new pane.
    libexec.install "src/margin"
    python = formula_opt_bin("python@3.14")/"python3.14"
    (bin/"margin").write <<~PY
      #!#{python}
      import sys
      sys.path.insert(0, "#{libexec}")
      from margin.cli import main
      main()
    PY
    chmod 0755, bin/"margin"
  end

  def caveats
    <<~EOS
      margin draws pages with the Kitty graphics protocol and types comments into
      the Claude Code pane through Zellij, so it also needs:
        brew install --cask ghostty        (or Kitty / WezTerm)
        brew install --cask claude-code
      Start Claude Code inside a Zellij pane, then check everything with:
        margin doctor
    EOS
  end

  test do
    assert_match "margin", shell_output("#{bin}/margin --help")
  end
end
