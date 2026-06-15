{
  description = "Socrates — prompt assistant with clarifying questions and extended reasoning";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonEnv = pkgs.python3.withPackages (
          ps: with ps; [
            fastapi
            uvicorn
            httpx
            textual
            hatchling
          ]
        );

        webDeps = pkgs.bun;

      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            webDeps
          ];
          shellHook = ''
            export PYTHONPATH="$(pwd)"
          '';
        };

        packages.socrates = pkgs.stdenv.mkDerivation {
          name = "socrates";
          src = ./.;
          buildInputs = [ pythonEnv ];
          installPhase = ''
            mkdir -p $out
            cp -r shared server tui web pyproject.toml $out/
          '';
        };
      }
    );
}
