class Mytool < Formula
  include Language::Python::Virtualenv

  desc "Awesome CLI tool"
  homepage "https://github.com/benmyrgorod/homebrew-leaptreegame"
  url "b9f93456d101211c0e31b96a11359d26977712d702b7793eacf50bd391552c98"
  sha256 "PUT_REAL_SHA256_HERE"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end
end
