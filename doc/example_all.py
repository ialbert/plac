import plac
import pathlib


@plac.pos('model', "Model name", choices=['A', 'B', 'C'])
@plac.opt('output_dir', "Optional output directory", type=pathlib.Path)
@plac.opt('n_iter', "Number of training iterations", type=int)
@plac.flg('debug', "Enable debug mode")
def main(model, output_dir='.', n_iter=100, debug=False):
    """A script for machine learning"""


if __name__ == '__main__':
    plac.call(main)
