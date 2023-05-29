{
  description = "Store dataclasses in SQLite. async.";

  outputs = { self, nixpkgs, flake-utils }:
    let
      deps = pyPackages: with pyPackages; [
        aiosqlite
      ];
      tools = pkgs: pyPackages: (with pyPackages; [
        pytest pytestCheckHook
        coverage pytest-cov
        mypy pytest-mypy
        yapf
        pytest-asyncio
      ] ++ [pkgs.ruff]);

      aiosqlitemydataclass-package = {pkgs, python3Packages}:
        python3Packages.buildPythonPackage {
          pname = "aiosqlitemydataclass";
          version = "0.0.1";
          src = ./.;
          format = "pyproject";
          propagatedBuildInputs = deps python3Packages;
          nativeBuildInputs = [ python3Packages.setuptools ];
          checkInputs = tools pkgs python3Packages;
        };

      overlay = final: prev: {
        pythonPackagesExtensions =
          prev.pythonPackagesExtensions ++ [(pyFinal: pyPrev: {
            aiosqlitemydataclass = final.callPackage aiosqlitemydataclass-package {
              python3Packages = pyFinal;
            };
          })];
      };
    in
      flake-utils.lib.eachDefaultSystem (system:
        let
          pkgs = import nixpkgs { inherit system; overlays = [ overlay ]; };
          defaultPython3Packages = pkgs.python311Packages;  # force 3.12

          aiosqlitemydataclass = pkgs.callPackage aiosqlitemydataclass-package {
            python3Packages = defaultPython3Packages;
          };
        in
        {
          devShells.default = pkgs.mkShell {
            buildInputs = [(defaultPython3Packages.python.withPackages deps)];
            nativeBuildInputs = tools pkgs defaultPython3Packages;
            shellHook = ''
              export PYTHONASYNCIODEBUG=1 PYTHONWARNINGS=error
            '';
          };
          packages.aiosqlitemydataclass = aiosqlitemydataclass;
          packages.default = aiosqlitemydataclass;
        }
    ) // { overlays.default = overlay; };
}
