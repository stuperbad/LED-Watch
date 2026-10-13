import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); print(pcbnew.ExportSpecctraDSN(b,sys.argv[2]))
