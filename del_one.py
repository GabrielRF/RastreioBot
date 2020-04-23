import sys

import db


if __name__ == '__main__':
    code = sys.argv[1]
    db.delete_package(code)
