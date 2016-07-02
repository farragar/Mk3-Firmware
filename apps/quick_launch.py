import ugfx
import os
import pyb
import badge

stay_here = 0
joy_updown = 0
joy_lr = 0


	
def callback_menu(line):
	global stay_here
	stay_here = 0
	print("Quitting")
	
def callback_arrow_up(line):
	global joy_updown
	joy_updown = 1
	
def callback_arrow_down(line):
	global joy_updown
	joy_updown = -1
	
def callback_arrow_right(line):
	global joy_lr
	joy_lr = 1
	
def callback_arrow_left(line):
	global joy_lr
	joy_lr = -1

def _move_arrow(x,y,cursor_loc, win_quick):
	
	arrow = [[0,0],[20,7],[0,14],[4,7]]
	
	win_quick.fill_polygon(cursor_loc[0]*150+4, cursor_loc[1]*35+14, arrow ,ugfx.WHITE)

	cursor_loc[0] += x
	cursor_loc[1] += y
	
	if cursor_loc[0] < 0:
		cursor_loc[0] = 0
	if cursor_loc[0] > 1:
		cursor_loc[0] = 1
		
	if cursor_loc[1] < 0:
		cursor_loc[1] = 0
	if cursor_loc[1] > 3:
		cursor_loc[1] = 3

	win_quick.fill_polygon(cursor_loc[0]*150+4, cursor_loc[1]*35+14, arrow ,ugfx.RED)


def main():
	wi = ugfx.width()
	hi = ugfx.height()
	b = badge.Badge()

	win_header = ugfx.Container(0,0,wi,30)
	win_quick = ugfx.Container(0,33,wi,hi-33-33)
	win_help = ugfx.Container(0,hi-30,wi,30)
	
	file_list = ["snake.py","party_mode.py"]
	
	while len(file_list) < 8:
		file_list.append("")
	file_list[7] = "View All"


	ugfx.set_default_font("D*")
	title = ugfx.Label(3,3,wi-10,45,"EMF Camp 2016",win_header)

	s = ugfx.Style()
	s.set_focus(ugfx.RED)

	ugfx.set_default_font("c*")
	ugfx.set_default_style(s)

	btn_c1r1 = ugfx.Button(25,5,100,30,file_list[0],win_quick)
	btn_c1r2 = ugfx.Button(25,40,100,30,file_list[1],win_quick)
	btn_c1r3 = ugfx.Button(25,75,100,30,file_list[2],win_quick)
	btn_c1r4 = ugfx.Button(25,110,100,30,file_list[3],win_quick)
	
	btn_c2r1 = ugfx.Button(180,5,100,30,file_list[4],win_quick)
	btn_c2r2 = ugfx.Button(180,40,100,30,file_list[5],win_quick)
	btn_c2r3 = ugfx.Button(180,75,100,30,file_list[6],win_quick)
	btn_c2r4 = ugfx.Button(180,110,100,30,file_list[7],win_quick)


	btn_ok = ugfx.Button(10,5,20,20,"A",win_help)
	l_ok = ugfx.Label(40,5,100,20,"Run",win_help)

	btn_back = ugfx.Button(100,5,20,20,"B",win_help)
	l_back = ugfx.Label(130,5,100,20,"Back",win_help)

	btn_menu = ugfx.Button(200,5,20,20,"M",win_help)
	l_back = ugfx.Label(230,5,100,20,"Menu",win_help)


	win_header.show()
	win_quick.show()
	win_help.show()

	#tgl_menu = pyb.Pin("BTN_MENU", pyb.Pin.IN)
	#extint1 = pyb.ExtInt(tgl_menu, pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_UP, None)
	#tgl_up = pyb.Pin("JOY_UP", pyb.Pin.IN)
	#extint2 = pyb.ExtInt(tgl_up, pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_DOWN, None)
	#tgl_down = pyb.Pin("JOY_DOWN", pyb.Pin.IN)
	#extint3 = pyb.ExtInt(tgl_down, pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_DOWN, None)
	#tgl_a = pyb.Pin("BTN_A", pyb.Pin.IN)
	#tgl_a.init(pyb.Pin.IN, pyb.Pin.PULL_UP)
	
	#enable_irq()
	
	b.init_pins()
	b.set_interrupt("BTN_MENU", callback_menu)
	b.set_interrupt("JOY_UP", callback_arrow_up)
	b.set_interrupt("JOY_DOWN", callback_arrow_down)
	b.set_interrupt("JOY_LEFT", callback_arrow_left)
	b.set_interrupt("JOY_RIGHT", callback_arrow_right)
			
	

	global stay_here
	global joy_updown
	global joy_lr
	stay_here = 1
	
	cursor_loc = [0, 0]

	while(stay_here):
		pyb.wfi()
		
		#if b.switch_up.value() == 1:
	#		cursor_loc = _move_arrow(1,0,cursor_loc, win_quick)
	#	if b.switch_down.value() == 1:
	#		cursor_loc = _move_arrow(-1,0,cursor_loc, win_quick)
	#	if b.switch_right.value() == 1:
	#		cursor_loc = _move_arrow(0,1,cursor_loc, win_quick)
	#	if b.switch_left.value() == 1:
	#		cursor_loc = _move_arrow(0,-1,cursor_loc, win_quick)
	
		if (joy_updown != 0) or (joy_lr != 0):
			_move_arrow(joy_lr, joy_updown, cursor_loc, win_quick)
			joy_updown = 0
			joy_lr = 0
		
		if b.switch_a.value() == 0:
			win_header.hide()
			win_quick.hide()
			win_help.hide()
			b.disable_interrupts()
			
			import snake
			snake.main()
			
			win_header.show()
			win_quick.show()
			win_help.show()
			b.set_interrupt("BTN_MENU", callback_menu)
			b.set_interrupt("JOY_UP", callback_arrow_up)
			b.set_interrupt("JOY_DOWN", callback_arrow_down)
			b.set_interrupt("JOY_LEFT", callback_arrow_left)
			b.set_interrupt("JOY_RIGHT", callback_arrow_right)
			
	b.disable_interrupts()
	
	btn_c1r1.destroy()
	btn_c1r2.destroy()
	btn_c1r3.destroy()
	btn_c1r4.destroy()	
	btn_c2r1.destroy()
	btn_c2r2.destroy()
	btn_c2r3.destroy()
	btn_c2r4.destroy()
	btn_ok.destroy()
	l_ok.destroy()
	btn_back.destroy()
	l_back.destroy()
	btn_menu.destroy()
	l_back.destroy()
	win_header.destroy()
	win_quick.destroy()
	win_help.destroy()
	title.destroy()


