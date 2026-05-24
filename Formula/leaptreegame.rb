class Leaptreegame < Formula
  include Language::Python::Virtualenv

  desc "Leap Tree Game is an experimental AI storytelling game"
  homepage "https://github.com/benmyrgorod/homebrew-leaptreegame"
  url "https://github.com/benmyrgorod/homebrew-leaptreegame/releases/download/v0.2.6/leaptreegame-0.2.6.tar.gz"
  sha256 "8ccaf122364b03a5ec21ae2e543d3a3a4f3cc5911f73c2084fae0ee8fa5e6356"
  license "MIT"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    system Formula["python@3.12"].opt_bin/"python3.12", "-m", "pip", "--python=#{venv.root}/bin/python", "install", "--no-cache-dir", "."

    bin.install_symlink (libexec/"bin/leaptreegame")
  end
end
