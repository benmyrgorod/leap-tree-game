class Leaptreegame < Formula
  include Language::Python::Virtualenv

  desc "Leap Tree Game is an experimental AI storytelling game"
  homepage "https://github.com/benmyrgorod/homebrew-leaptreegame"
  url "https://github.com/benmyrgorod/homebrew-leaptreegame/releases/download/v0.3.0/leaptreegame-0.3.0.tar.gz"
  sha256 "80698e78c27840ecc67fee2cd1b7090999c3ff9d863fa9a3d0313ba21b74535e"
  license "MIT"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    system Formula["python@3.12"].opt_bin/"python3.12", "-m", "pip", "--python=#{venv.root}/bin/python", "install", "--no-cache-dir", "."

    bin.install_symlink (libexec/"bin/leaptreegame")
  end
end
