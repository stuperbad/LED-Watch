import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); print("import ok:",pcbnew.ImportSpecctraSES(b,sys.argv[2])); pcbnew.SaveBoard(sys.argv[3],b)
