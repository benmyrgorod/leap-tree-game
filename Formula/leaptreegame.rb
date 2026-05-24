class Leaptreegame < Formula
  include Language::Python::Virtualenv

  desc "Leap Tree Game is an experimental AI storytelling game"
  homepage "https://github.com/benmyrgorod/homebrew-leaptreegame"
  url "https://github.com/benmyrgorod/homebrew-leaptreegame/releases/download/v0.2.8/leaptreegame-0.2.8.tar.gz"
  sha256 "878d74b2de6bcdd42171902a5ead3cf389786f1e852d12ec8f1df7ba9d42f06a"
  license "MIT"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    system Formula["python@3.12"].opt_bin/"python3.12", "-m", "pip", "--python=#{venv.root}/bin/python", "install", "--no-cache-dir", "."

    bin.install_symlink (libexec/"bin/leaptreegame")
  end
end
