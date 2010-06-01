def main(arg: "required argument"):
   "do something with arg"
   print('Got %s' % arg)

if __name__ == '__main__':
    import plac; plac.call(main) # passes sys.argv[1:] to main
