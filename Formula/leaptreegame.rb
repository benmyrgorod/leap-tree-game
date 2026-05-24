class Leaptreegame < Formula
  include Language::Python::Virtualenv

  desc "Leap Tree Game is an experimental AI storytelling game"
  homepage "https://github.com/benmyrgorod/homebrew-leaptreegame"
  url "https://github.com/benmyrgorod/homebrew-leaptreegame/releases/download/v0.2.3/leaptreegame-0.2.3.tar.gz"
  sha256 "a790a4feda3a6c2376f72959ef233d3635f8c76579c2ba3d3a1b0ee3d7bac21c"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end
end
