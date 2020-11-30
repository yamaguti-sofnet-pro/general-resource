import curses
import random
import time
from collections import deque
from multiprocessing import Process, Queue
import threading
import sys
args = sys.argv
# sem_open が有効ならば、起動時引数`-C`で起動すること
semValid = True if (1 < len(sys.argv)) and (args[ 1 ] == '-C') else False

def loop(stdscr, *args, **kwds):
  global barea
  barea = BattleArea()
  barea.init(stdscr)
  #TODO: ランダム配置か任意の配置を選択できるようにする
  ryx = barea.randcoordinate(4)
  global se
  se = [
    Piece(0, ryx[0], ryx[1], 2, 3),
    Piece(1, ryx[2], ryx[3], 3, 2),
    Piece(2, ryx[4], ryx[5], 3, 2),
    Piece(3, ryx[6], ryx[7], 3, 2)]
  ryx = barea.randcoordinate(4)
  global so
  so = [
    Piece(0, ryx[0], ryx[1], 2, 3),
    Piece(1, ryx[2], ryx[3], 3, 2),
    Piece(2, ryx[4], ryx[5], 3, 2),
    Piece(3, ryx[6], ryx[7], 3, 2)]
  global ope
  ope = so[0]
  ch = 0
  # まずスクリーン全体を描画してから 
  barea.draw()
  for s1 in so:
    s1.draw()
  barea.prompt("{}:[{}{}]Order or '?'".format(ope.id, int2abc(Caret.x), str(Caret.y)))
  barea.guide()
  # カレットを描画する
  global caret
  caret = Caret(ryx[0], ryx[1])
  myTurn = True
  if semValid:
    caret.start()
  while True:
    command = ''
    # スクリーン全体を描画する
    barea.draw()
    for s1 in so:
      s1.draw()
    if not semValid:
      caret.draw()
    if myTurn:
      if ope == None:
        barea.prompt("*[{}{}]Press 'q'".format(int2abc(Caret.x), str(Caret.y)))
      else:
        barea.prompt("{}:[{}{}]Order or '?'".format(ope.id, int2abc(Caret.x), str(Caret.y)))
      # キーボード入力を取得する
      ch = getcho() if kbhit() else 0
      if ch != 0:
        if ch == ord('q') or ch == 3: # ETX テキスト終了
          break
        elif ch == ord('?'):
          barea.guide()
        elif ord('0') <= ch and ch <= ord('3'):
          i = ch - ord('0')
          isExist = False
          for s2 in so:
            if s2.id == i:
              isExist = True
          if isExist:
            if semValid:
              q.put([-1, -1])
            ope, Caret.y, Caret.x = so[i], so[i].y, so[i].x
          if semValid:
            q.put([Caret.y, Caret.x])
        elif ch == ord('m'):
          command = 'Moved to'
          if commandMoveto():
            barea.info("S{} {} {}{}".format(ope.id, command, int2abc(Caret.x), str(Caret.y)))
            myTurn = not myTurn if 0 < len(se) else True
        elif ch == ord('a'):
          command = 'Attacked'
          result, sank = commandAttack()
          if result != "  ":
            barea.info("S{} {} {}{}: {}".format(ope.id, command, int2abc(Caret.x), str(Caret.y), result))
            if result == "**":
              barea.info("Enemy ship #{} sank.".format(sank))
              if len(se) <= 0:
                barea.info(" W W   OOO  N   N")
                barea.info(" W W  O   O N  NN")
                barea.info("W W W O   O N N N")
                barea.info("W W W O   O NN  N")
                barea.info("W W W  OOO  N   N")
                barea.info(" ")
                barea.info("  Y    OOO   UUU")
                barea.info("  Y   O   O U   U")
                barea.info("  Y   O   O U   U")
                barea.info(" Y Y  O   O U   U")
                barea.info("Y   Y  OOO  U   U")
            myTurn = not myTurn if 0 < len(se) else True
        elif ch == ord('+'):
          command = 'Mark'
        elif ch == ord('-'):
          command = 'Unmark'
        elif ch == 27: # ESC エスケープ
          ch = getcho()
          if ch == ord('O'): # is not '[' for some reason.
            ch = getcho()
            if semValid:
              q.put([-1, -1])
            if ch == ord('A') and ((Caret.x + 1) % 2 < Caret.y): # KEY_UP:
              Caret.y -= 1
            elif ch == ord('B') and (Caret.y < barea.max_y - 1): # KEY_DOWN:
              Caret.y += 1
            elif ch == ord('C') and (0 < Caret.y and Caret.x < barea.max_x - 1): # KEY_RIGHT:
              Caret.x += 1
            elif ch == ord('D') and (0 < Caret.y and 0 < Caret.x): # KEY_LEFT:
              Caret.x -= 1
            if semValid:
              q.put([Caret.y, Caret.x])
          else:
            continue
    elif 0 < len(se):
      result, sank = enemysTurn()
      if result != "  ":
        if result == "**":
          barea.info("Own ship #{} sank.".format(sank))
          if len(so) <= 0:
            barea.info("LLLL  OO  SSS  EEE")
            barea.info("L    O  O    S E  ")
            barea.info("L    O  O  SS  EEE")
            barea.info("L    O  O S    E  ")
            barea.info("L     OO   SSS EEE")
            barea.info(" ")
            barea.info("  Y    OOO   UUU")
            barea.info("  Y   O   O U   U")
            barea.info("  Y   O   O U   U")
            barea.info(" Y Y  O   O U   U")
            barea.info("Y   Y  OOO  U   U")
      myTurn = not myTurn if 0 < len(se) else True

def enemysTurn():
  result, sank = "  ", -1
  action = random.randrange(0, 3) + random.randrange(0, 3)
  if action != 2:
    # move
    i = random.randrange(0, len(se))
    isOutOfRange = True
    while isOutOfRange:
      dx = random.randrange(-1 * se[i].speed, se[i].speed + 1)
      dy = random.randrange(-1 * se[i].speed, se[i].speed + 1)
      x = se[i].x + dx
      y = se[i].y + dy
      distance = dxy(se[i].x, se[i].y, x, y)
      if 0 <= x and x < barea.max_x and \
        0 <= y and y < barea.max_y and \
        distance != 0 and distance <= se[i].speed and \
        ((x + 1) % 2 <= y):
        #DEBUG: barea.info("{}:{}:{}:{}:{}".format(i, dx, dy, x, y))
        isOutOfRange = False
        log = ""
        l1 = list(range(0, dy)) if 0 < dy else list(range(dy, 0))
        for l in l1:
          if dy < 0:
            log += "^ "
          elif 0 < dy:
            log += "v "
        l1 = list(range(0, dx)) if 0 < dx else list(range(dx, 0))
        for l in l1:
          if dx < 0:
            log += "< "
          elif 0 < dx:
            log += "> "
        se[i].x, se[i].y = x, y
    barea.info("Enemy mov. " + log)
  else:
    # attack
    i = random.randrange(0, len(se))
    isOutOfRange = True
    while isOutOfRange:
      dx = random.randrange(-1 * se[i].range, se[i].range + 1)
      dy = random.randrange(-1 * se[i].range, se[i].range + 1)
      x = se[i].x + dx
      y = se[i].y + dy
      distance = dxy(se[i].x, se[i].y, x, y)
      if 0 <= x and x < barea.max_x and \
        0 <= y and y < barea.max_y and \
        distance != 0 and distance <= se[i].range and \
        ((x + 1) % 2 <= y):
        isOutOfRange = False
        cy = y * 2 + (x % 2)
        cx = x * 3 + 3
        win0.addstr(cy - 1, cx, "__", curses.color_pair(1))
        win0.addstr(cy, cx - 1, "/", curses.color_pair(1))
        win0.addstr(cy, cx + 2, "\\", curses.color_pair(1))
        win0.addstr(cy + 1, cx - 1, "\__/", curses.color_pair(1))
        win0.refresh(); time.sleep(1.0)
        win0.addstr(cy, cx, "**", curses.color_pair(1)); win0.refresh(); time.sleep(0.2)
        win0.addstr(cy, cx, "++", curses.color_pair(0)); win0.refresh(); time.sleep(0.1)
        win0.addstr(cy, cx, "..", curses.color_pair(4)); win0.refresh(); time.sleep(0.3)
        distance = 999
        for s1 in so:
          d1 = dxy(x, y, s1.x, s1.y)
          if d1 < distance:
            distance = d1
          if d1 == 0:
            sank = s1.id
            if s1 == ope: #BUG: 'ope' referenced before assignment.
              if 0 < len(so):
                for s2 in so:
                  if s2.id != sank:
                    ope = s2
                    break
              else:
                ope = None
            so.remove(s1)
            break
        if distance == 0:
          result = "**"
          win0.addstr(cy, cx, "##", curses.color_pair(3)); win0.refresh(); time.sleep(0.1)
          win0.addstr(cy, cx, result, curses.color_pair(1)); win0.refresh()
          print("\007"); print("\007"); time.sleep(1.5); print("\007")
        elif distance == 1:
          result = "ww"
          win0.addstr(cy, cx, result, curses.color_pair(3)); win0.refresh(); time.sleep(1.5)
        elif distance == 2:
          result = "~~"
          win0.addstr(cy, cx, result, curses.color_pair(4)); win0.refresh(); time.sleep(1.5)
        else:
          result = "__"
          win0.addstr(cy, cx, result, curses.color_pair(4)); win0.refresh(); time.sleep(0.5)

    barea.info("Enemy Atked {}{}: {}".format(int2abc(x), str(y), result))
  #DEBUG: start
  # debug = ""
  # for s1 in se:
  #   debug += int2abc(s1.x) + str(s1.y) + " "
  # barea.info(debug)
  #DEBUG: end
  return result, sank

def roundup(x):
  return int(x // 1 + (0 < (x % 1)))

def rounddown(x):
  return int(x // 1)

def dxy(x1, y1, x2, y2):
  ''' 座標(y1, x1)-(y2, x2)の距離を返す '''
  dy = abs(y2 - y1)
  dx = abs(x2 - x1)
  if ((x1 % 2) == 0 and y2 < y1) or ((x1 % 2) != 0 and y1 < y2):
    distance = dy + dx - (dy if dy <= roundup(dx / 2) else roundup(dx / 2))
  else:
    distance = dy + dx - (dy if dy <= rounddown(dx / 2) else rounddown(dx / 2))
  return distance

def commandMoveto():
  result = False
  if ope != None:
    distance = dxy(ope.x, ope.y, Caret.x, Caret.y)
    if distance <= ope.speed:
      ope.y, ope.x = Caret.y, Caret.x
      result = True
    else:
      print("\007")
  else:
    print("\007")
  return result

def commandAttack():
  distance = 999
  result = "  "
  if ope != None:
    range = dxy(ope.x, ope.y, Caret.x, Caret.y)
    sank = -1
    if range != 0 and range <= ope.range:
      cy = Caret.y * 2 + (Caret.x % 2)
      cx = Caret.x * 3 + 3
      win0.addstr(cy - 1, cx, "__", curses.color_pair(1))
      win0.addstr(cy, cx - 1, "/", curses.color_pair(1))
      win0.addstr(cy, cx + 2, "\\", curses.color_pair(1))
      win0.addstr(cy + 1, cx - 1, "\__/", curses.color_pair(1))
      win0.refresh(); time.sleep(0.3)
      win0.addstr(cy, cx, "**", curses.color_pair(1)); win0.refresh(); time.sleep(0.2)
      win0.addstr(cy, cx, "++", curses.color_pair(0)); win0.refresh(); time.sleep(0.1)
      win0.addstr(cy, cx, "..", curses.color_pair(4)); win0.refresh(); time.sleep(0.3)
      for s1 in se:
        d1 = dxy(Caret.x, Caret.y, s1.x, s1.y)
        if d1 < distance:
          distance = d1
        if d1 == 0:
          sank = s1.id
          se.remove(s1)
          break
      if distance == 0:
        result = "**"
        win0.addstr(cy, cx, "##", curses.color_pair(3)); win0.refresh(); time.sleep(0.1)
        win0.addstr(cy, cx, result, curses.color_pair(1)); win0.refresh()
        print("\007"); print("\007"); time.sleep(1.5); print("\007")
      elif distance == 1:
        result = "ww"
        win0.addstr(cy, cx, result, curses.color_pair(3)); win0.refresh(); time.sleep(1.5)
      elif distance == 2:
        result = "~~"
        win0.addstr(cy, cx, result, curses.color_pair(4)); win0.refresh(); time.sleep(1.5)
      else:
        result = "__"
        win0.addstr(cy, cx, result, curses.color_pair(4)); win0.refresh(); time.sleep(0.5)
    else:
      print("\007")
  else:
    print("\007")
  return result, sank

class BattleArea:
  LOG_WIDTH = 7 # ログ表示桁数を(7 * 3 - 1)桁にする
  LOG_WIDTH = LOG_WIDTH + (LOG_WIDTH % 2) 

  def init(self, stdscr):
    global win0
    win0 = curses.initscr()
    win0.clear()
    curses.start_color()
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_RED,     curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE,    curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_BLACK,   curses.COLOR_GREEN)
    BattleArea.max_height, BattleArea.max_width = win0.getmaxyx()
    BattleArea.max_y = (BattleArea.max_height - 1) // 2
    x = (BattleArea.max_width - 2) // 3
    BattleArea.max_x = x - (x % 2 - 1) - BattleArea.LOG_WIDTH
    # BattleArea.map = [[0] * BattleArea.max_y for i in range(BattleArea.max_x) for j in range(2)]
    BattleArea.log = deque([], (BattleArea.max_y + 1) * 2)
    if semValid:
      global q
      q = Queue()
    random.seed()

  def draw(self):
    for x in range(0, BattleArea.max_x):
      win0.addstr(0, x * 3 + 3, int2abc(x))
      if (x < 26) and (x % 2 != 0):
        win0.addstr(0, x * 3 + 4, '_', curses.color_pair(4))
    b0 = ["\__/  "] * 100
    b1 = "".join(b0)
    win0.addstr(1, 0, " 0")
    for y in range(0, BattleArea.max_y):
      win0.addstr((y * 2) + 1, 2, b1[0:(BattleArea.max_x) * 3 + 1], curses.color_pair(4))
      if y < BattleArea.max_y - 1:
        win0.addstr((y * 2) + 2, 0, ("  " + str(y + 1))[-2:])
      win0.addstr((y * 2) + 2, 2, b1[3:(BattleArea.max_x) * 3 + 4], curses.color_pair(4))

  def drawRange(self, y, x, r):
    ''' 座標(y, x)から距離rの範囲を表示する '''
    pass

  def info(self, msg):
    ''' ログを1行目以降に表示する '''
    m = (msg + (" " * (BattleArea.LOG_WIDTH * 3)))[:((BattleArea.LOG_WIDTH - 1) * 3)]
    BattleArea.log.append(m)
    l = len(BattleArea.log)
    for iy in range(1, l - 2): #TODO: l - 1
      win0.addstr(iy, BattleArea.max_x * 3 + 4, BattleArea.log[l - iy], curses.color_pair(0))
    win0.refresh()

  def prompt(self, msg):
    ''' プロンプトを0行目に表示する '''
    m = (msg + (" " * (BattleArea.LOG_WIDTH * 3)))[:((BattleArea.LOG_WIDTH - 1) * 3)]
    win0.addstr(0, BattleArea.max_x * 3 + 4, m, curses.color_pair(3))
    win0.refresh()

  def guide(self):
    barea.info("_" * 20)
    barea.info("Q)uit")
    barea.info("-) unmark")
    barea.info("+) mark")
    barea.info("A)ttack")
    barea.info("M)ove to")
    barea.info("3) piece S3")
    barea.info("2) piece S2")
    barea.info("1) piece S1")
    barea.info("0) piece S0")
    if 0 < len(se):
      barea.info("{} Enemy ships left.".format(len(se)))
    else:
      barea.info("No Enemy ship left.")
    barea.info("_" * 20)

  def randcoordinate(self, n):
    ''' 指定数のユニットが重ならないように座標を乱数で決める '''
    yx = []
    for i in range(0, n):
      y, x = 0, 0
      while y == 0 and x % 2 == 0:
        y = random.randint(0, BattleArea.max_y - 1)
        x = random.randint(0, BattleArea.max_x - 1)
        if 0 < i:
          for j in range(0, i - 1):
            if y == yx[j * 2] and x == yx[j * 2 + 1]:
              y, x = 0, 2
              break
      yx.append(y)
      yx.append(x)
    return yx

class Piece:
  ''' 駒 '''
  def __init__(self, id, y, x, speed, range):
    self.id = id
    self.y = y
    self.x = x
    self.speed = speed
    self.range = range

  def draw(self):
    win0.addstr(self.y * 2 + (self.x % 2), self.x * 3 + 3, "S" + str(self.id), curses.color_pair(2))

if semValid:
  class Caret(Process):
    y, x = 0, 0
    def __init__(self, y, x):
      Process.__init__(self)
      self.daemon = True
      Caret.y, Caret.x = y, x

    def run(self):
      caret_color = [curses.color_pair(3), curses.color_pair(4), curses.color_pair(6)]
      cc = 0
      cyx = [Caret.y, Caret.x]
      while True:
        if not q.empty():
          cyx = q.get()
        cy = Caret.y * 2 + (Caret.x % 2)
        cx = Caret.x * 3 + 3
        if cyx[0] != -1 and cyx[1] != -1:
          Caret.y, Caret.x = cyx[0], cyx[1]
          win0.addstr(cy + 1, cx, "__", caret_color[(2 + cc) % 3])
          win0.addstr(cy + 1, cx - 1, "\\", caret_color[(1 + cc) % 3])
          win0.addstr(cy, cx - 1, "/", caret_color[cc % 3])
          if 0 < Caret.y:
            win0.addstr(cy - 1, cx, "__", caret_color[(2 + cc) % 3])
          elif (0 < Caret.y) or (0 == Caret.y and Caret.x < 26):
            win0.addstr(cy - 1, cx + 1, "_", caret_color[(2 + cc) % 3])
          win0.addstr(cy, cx + 2, "\\", caret_color[(1 + cc) % 3])
          win0.addstr(cy + 1, cx + 2, "/", caret_color[cc % 3])
          cc = cc + 1 if cc < 2 else 0
          win0.refresh()
          time.sleep(0.33)
        else:
          win0.addstr(cy + 1, cx, "__", curses.color_pair(4))
          win0.addstr(cy + 1, cx - 1, "\\", curses.color_pair(4))
          win0.addstr(cy, cx - 1, "/", curses.color_pair(4))
          if 0 < Caret.y:
            win0.addstr(cy - 1, cx, "__", curses.color_pair(4))
          elif (0 < Caret.y) or (0 == Caret.y and Caret.x < 26):
            win0.addstr(cy - 1, cx + 1, "_", curses.color_pair(4))
          win0.addstr(cy, cx + 2, "\\", curses.color_pair(4))
          win0.addstr(cy + 1, cx + 2, "/", curses.color_pair(4))
          time.sleep(0.33)
else:
  class Caret(threading.Thread):
    y, x = 1, 1
    def __init__(self, y, x):
      Caret.y, Caret.x = y, x

    def draw(self):
      cy = Caret.y * 2 + (Caret.x % 2)
      cx = Caret.x * 3 + 3
      # win0.addstr(cy - 1, cx, "__", curses.color_pair(7))
      win0.addstr(cy, cx - 1, "/", curses.color_pair(7))
      win0.addstr(cy, cx + 2, "\\", curses.color_pair(7))
      win0.addstr(cy + 1, cx - 1, "\__/", curses.color_pair(7))

def int2abc(in1):
  BASE = 26
  blist = [BASE]
  l = len(blist) - 1
  while blist[l] <= in1:
    l = len(blist)
    blist.append(BASE ** (l + 1) + blist[l - 1])
  abc = ""
  for col in range(len(blist) - 1, -1, -1):
    if 1 < col:
      a = (in1 - blist[col - 2]) // (BASE ** col)
    else:
      a = in1 // (BASE ** col)
    if 0 < col:
      abc += ("" + chr(a + 64))
    else:
      abc += ("" + chr(a + 65))
    in1 -= a * (BASE ** col)
  return abc

def getcho():
  cho = ord(getch())
  return cho

# kbhit http://code.activestate.com/recipes/572182-how-to-implement-kbhit-on-linux
import sys, termios, atexit
from select import select

# save the terminal settings
fd = sys.stdin.fileno()
new_term = termios.tcgetattr(fd)
old_term = termios.tcgetattr(fd)

# new terminal setting unbuffered
new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)

# switch to normal terminal
def set_normal_term():
  termios.tcsetattr(fd, termios.TCSAFLUSH, old_term)

# switch to unbuffered terminal
def set_curses_term():
  termios.tcsetattr(fd, termios.TCSAFLUSH, new_term)

def putch(ch):
  sys.stdout.write(ch)

def getch():
  return sys.stdin.read(1)

def getche():
  ch = getch()
  putch(ch)
  return ch

def kbhit():
  dr,dw,de = select([sys.stdin], [], [], 0)
  return dr != []

if __name__ == '__main__':
  atexit.register(set_normal_term)
  set_curses_term()
  curses.wrapper(loop)
