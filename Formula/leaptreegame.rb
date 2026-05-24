class Leaptreegame < Formula
  include Language::Python::Virtualenv

  desc "Leap Tree Game is an experimental AI storytelling game"
  homepage "https://github.com/benmyrgorod/homebrew-leaptreegame"
  url "https://github.com/benmyrgorod/homebrew-leaptreegame/releases/download/v0.2.4/leaptreegame-0.2.4.tar.gz"
  sha256 "7f3cf2ec96b73cbbab0e69ebeb7c97ba9bc630fa2f94b189e5ab245bba16fbe5"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end
end
