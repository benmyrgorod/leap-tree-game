class Leaptreegame < Formula
  include Language::Python::Virtualenv

  desc "Leap Tree Game is an experimental AI storytelling game"
  homepage "https://github.com/benmyrgorod/homebrew-leaptreegame"
  url "https://files.pythonhosted.org/packages/ad/f1/14842f250d4f1707720231ffa335c38f7659799f20a4ad187b96515685f3/leaptreegame-0.2.0.tar.gz"
  sha256 "b9f93456d101211c0e31b96a11359d26977712d702b7793eacf50bd391552c98"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end
end
