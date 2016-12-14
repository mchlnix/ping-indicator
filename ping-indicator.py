#!/usr/bin/python2.7 -u

# Removes log functionality again
# Now writes avg ping to log
# Now keeps track of sent and lost pings and writes it to .config/pingindicator/ping.log
# Now resets instantly
# Now resets the indicator icon as well
# Removed the string representation
# Added Min and Max information
# Fixed stderr leaking into terminal
# Now only prints used timeout, when one was given via commandline argument
# Code now fits on 80 character terminals
# Now updates the menu even when timeouts happen
# Now tricks xfce4-panel, caching icons by path

from appindicator import Indicator, STATUS_ACTIVE, STATUS_ATTENTION
from appindicator import CATEGORY_SYSTEM_SERVICES
from collections import deque
from subprocess import check_output, CalledProcessError, STDOUT
from ImageDraw import Draw
from gobject import timeout_add
from os.path import expanduser
from random import random
from Image import new
from time import strftime
from gtk import Menu, MenuItem, SeparatorMenuItem, main, main_quit
from sys import argv, exit
from os import makedirs

timeout = 2000 # in ms
packet_amount = 22 # also width of indicator icon in pixels
min_scale = 1./100 # in 1/ms
indicator_image_height = 22 # in unity
mid_thres = 2/3.  # of timeout
good_thres = 1/3. # of timeout
destination = '8.8.8.8' # google dns server

avg = lambda x :  int( sum( x ) / len( x ) )


class PingIndicator():

    def __init__( self ):
        self.path = make_path()
        self.icon = new( 'RGBA', ( packet_amount, indicator_image_height ) )
        self.icon.save( self.path )

        self.LABEL_GUIDE = '9999'
        self.online = True

        self.packets = deque( [], packet_amount )
        
        self.lost = 0
        self.sent = 0

        self.indicator = Indicator( id='ping-indicator',
                                    icon_name='ping-indicator',
                                    category=CATEGORY_SYSTEM_SERVICES,
                                    icon_theme_path='/tmp/',
                                  )
        self.indicator.set_status( STATUS_ACTIVE )

        menu_item_name     = MenuItem( 'Ping: Internet' )
        menu_separator     = SeparatorMenuItem()
        menu_item_since    = MenuItem( 'Online since: '
                                        + strftime( '%H:%M:%S' ) )
        menu_item_packets1 = MenuItem( 'Lost: -, Avg: -' )
        menu_item_packets2 = MenuItem( 'Max: -, Min: -'  )
        menu_separator2    = SeparatorMenuItem()
        menu_item_reset    = MenuItem( 'Reset' )
        menu_item_exit     = MenuItem( 'Exit'  )
        menu_item_exit.connect(  'activate', self.stop  )
        menu_item_reset.connect( 'activate', self.reset )

        indicator_menu = Menu()
        indicator_menu.append( menu_item_name     )
        indicator_menu.append( menu_separator     )
        indicator_menu.append( menu_item_since    )
        indicator_menu.append( menu_item_packets1 )
        indicator_menu.append( menu_item_packets2 )
        indicator_menu.append( menu_separator2    )
        indicator_menu.append( menu_item_reset    )
        indicator_menu.append( menu_item_exit     )
        indicator_menu.show_all()

        self.indicator.set_menu( indicator_menu )

        timeout_add( int(timeout*1.05), self.update_indicator )

    def stop( self, widget=None ):
        main_quit()


    def update_icon( self ):
        self.path = make_path()
        self.indicator.set_icon( self.path )

        draw = Draw( self.icon )

        (width, height) = self.icon.size
        width -= 1
        height -= 1

        for i in range( height+1 ):
            draw.line( (0, i, width, i ), fill=(0,0,0,0) )

        try:
            scale = min( 1./max( self.packets ), min_scale )
        except ValueError:
            scale = min_scale


        for ( index, ping ) in enumerate( list( reversed( self.packets ) ) ):
            x = ping/float( timeout )

            color = ( int( -324 * x**2 + 390 * x + 138 ), #R
                      int( -480 * x**2 + 254 * x + 226 ), #G
                      int( -212 * x**2 + 160 * x + 52 ),  #B
                      255,
                    )

            draw.line( ( width - index, height, width - index,
                         height - int ( scale * ping * height ) ),
                         fill=color
                     )

        del draw             # Seen in example, unsure if necessary

        self.icon.save( self.path )

        self.indicator.set_status( STATUS_ATTENTION ) # Needed, so that the
        self.indicator.set_status( STATUS_ACTIVE )    # icon updates itself


    def update_indicator( self ):

        #new_label = 'offline'

        self.sent += 1

        try:
            output = check_output( [ 'ping', '-c', '1', '-W', str(timeout/1000),
                                     destination,
                                   ],
                                   stderr=STDOUT,
                                 ) # man ping

            for line in output.splitlines():
                pos = line.find( 'time=' )
                if pos != -1:
                    new_label = line[ pos + 5 : -3 ].center( 4 )
                    self.packets.append( round( float( new_label ), 2 ) )

                    if not self.online:
                        self.online = True
                        self.indicator.get_menu().get_children()[2].set_label(
                                   'Last disconnect: ' + strftime( '%H:%M:%S' ),
                                                                             )
                    break
        except CalledProcessError:
            self.lost += 1
            self.packets.append( timeout )

            if self.online:
                self.online = False
                self.indicator.get_menu().get_children()[2].set_label(
                                      'Offline since: ' + strftime( '%H:%M:%S' )
                                                                     )

        self.update_icon()
        self.update_menu()

        return True


    def reset( self, widget=None ):
        self.packets.clear()
        self.update_icon()
        self.indicator.get_menu().get_children()[2].set_label( 'Online since: '
                                                       + strftime( '%H:%M:%S' ),
                                                             )
        self.indicator.get_menu().get_children()[3].set_label('Lost: -, Avg: -')
        self.indicator.get_menu().get_children()[4].set_label('Max: -, Min: -' )


    def run( self ):
        main()


    def update_menu( self ):
        self.indicator.get_menu().get_children()[3].set_label(
                        'Lost: %d, Avg: %dms' %
                        ( self.packets.count( timeout ), avg( self.packets ) ),
                                                             )
        self.indicator.get_menu().get_children()[4].set_label(
                        'Max: %dms, Min: %dms' %
                        ( max( self.packets ), min( self.packets ) ),
                                                             )

def make_path():
    return '/tmp/' + str(int(random() * 10)) + '.png'

if __name__ == '__main__':
    if len(argv) > 1:
        try:
            timeout = int( argv[1] )
            print 'Using timeout: ' + str(timeout) + 'ms'
        except ValueError:
            print 'Usage: pingindicator [timeout in milliseconds / -h, --help]'
            exit()

    PingIndicator().run()
