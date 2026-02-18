import sys
import os
import ctypes
import winreg

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def register_association():
    """
    Registers .mpgif extension to open with this python script (main.py play).
    Uses HKCU so admin rights are NOT generally required for per-user association.
    """
    
    built_exe = os.path.abspath("dist/MPGIF Reader.exe")
    script_path = os.path.abspath("main.py")
    python_exe = sys.executable
    
    if os.path.exists(built_exe):
        command = f'"{built_exe}" play "%1"'
        
        possible_icon = os.path.abspath("deployment/mpgif_logo.ico")
        if os.path.exists(possible_icon):
            icon_path = possible_icon
        else:
            icon_path = built_exe
            
        print(f"🔗 Executable: {built_exe}")
    else:
        command = f'"{python_exe}" "{script_path}" play "%1"'
        icon_path = os.path.abspath("deployment/mpgif_logo.ico")
        if not os.path.exists(icon_path):
            icon_path = python_exe 
        print(f"🔗 Script: {script_path}")
    
    prog_id = "MPGIF.File"
    ext = ".mpgif"
    file_type_desc = "MPGIF Reader"
    
    print(f"Registering {ext}...\nCommand: {command}")

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, file_type_desc)

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}\\DefaultIcon") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, icon_path)
            
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}\\shell\\open\\command") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, command)

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, prog_id)
            
        try:
             ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, 0, 0)
        except Exception as e:
            print(f"Warning notifying explorer: {e}")

        print("✅ Association réussie ! Vous pouvez maintenant double-cliquer sur un fichier .mpgif.")
        print("(Note : Si ça ne marche pas immédiatement, redémarrez l'explorateur ou choisissez 'Ouvrir avec' -> 'Chercher une autre application' sur le pc une première fois)")

    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement dans le registre : {e}")
        print("Essayez de lancer le script en tant qu'administrateur si cela échoue.")

if __name__ == "__main__":
    register_association()
    input("Appuyez sur Entrée pour quitter...")
