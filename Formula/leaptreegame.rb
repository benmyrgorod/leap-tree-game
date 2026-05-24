class Leaptreegame < Formula
  include Language::Python::Virtualenv

  desc "Leap Tree Game is an experimental AI storytelling game"
  homepage "https://github.com/benmyrgorod/homebrew-leaptreegame"
  url "https://github.com/benmyrgorod/homebrew-leaptreegame/releases/download/v0.3.2/leaptreegame-0.3.2.tar.gz"
  sha256 "b75e692388db42d07326692dc1a5584c34733c0d2844a5d2428d5a851ed6d4e1"
  license "MIT"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    system Formula["python@3.12"].opt_bin/"python3.12", "-m", "pip", "--python=#{venv.root}/bin/python", "install", "--no-cache-dir", "."

    bin.install_symlink (libexec/"bin/leaptreegame")
  end
end
