{pkgs}: {
  deps = [
    pkgs.wget
    pkgs.geckodriver
    pkgs.awscli2
    pkgs.lsof
    pkgs.chromium
    pkgs.chromedriver
  ];
}
