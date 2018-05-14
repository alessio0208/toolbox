import shutil
from os import environ, chdir
from os.path import isdir, isfile, join, abspath
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxDriver
import tbselenium.common as cm
from tbselenium.utils import prepend_to_env_var, is_busy
from tbselenium.tbbinary import TBBinary
from tbselenium.exceptions import (TBDriverConfigError, TBDriverPortError,
                                   TBDriverPathError)
# AM: Start modification!
import time, os
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from PIL import Image
# AM: End modification!

try:
    from httplib import CannotSendRequest
except ImportError:
    from http.client import CannotSendRequest


class TorBrowserDriver(FirefoxDriver):
    """
    Extend Firefox webdriver to automate Tor Browser.
    """
    def __init__(self,
                 tbb_path="",
                 tor_cfg=cm.LAUNCH_NEW_TBB_TOR,
                 tbb_fx_binary_path="",
                 tbb_profile_path="",
                 tbb_logfile_path="",
                 tor_data_dir="",
                 pref_dict={},
                 socks_port=None,
                 control_port=None,
                 extensions=[],
                 default_bridge_type="",
                 capabilities=None):

        self.tor_cfg = tor_cfg
        self.setup_tbb_paths(tbb_path, tbb_fx_binary_path,
                             tbb_profile_path, tor_data_dir)
        self.profile = webdriver.FirefoxProfile(self.tbb_profile_path)
        self.install_extensions(extensions)
        self.init_ports(tor_cfg, socks_port, control_port)
        self.init_prefs(pref_dict, default_bridge_type)
        self.setup_capabilities(capabilities)
        # AM: Start modification!
        self.capabilities['acceptSslCerts'] = True
        # AM: End modification! 
        self.export_env_vars()
        self.binary = self.get_tb_binary(logfile=tbb_logfile_path)
        self.binary.add_command_line_options('--class', '"Tor Browser"')
        super(TorBrowserDriver, self).__init__(firefox_profile=self.profile,
                                               firefox_binary=self.binary,
                                               capabilities=self.capabilities,
                                               timeout=cm.TB_INIT_TIMEOUT,
                                               log_path=tbb_logfile_path)
        self.is_running = True
        sleep(1)

    def install_extensions(self, extensions):
        for extension in extensions:
            self.profile.add_extension(extension)

    def init_ports(self, tor_cfg, socks_port, control_port):
        """Check SOCKS port and Tor config inputs."""
        if tor_cfg not in [cm.USE_RUNNING_TOR, cm.LAUNCH_NEW_TBB_TOR]:
            raise TBDriverConfigError("Unrecognized tor_cfg: %s" % tor_cfg)

        if socks_port is None:
            if tor_cfg == cm.USE_RUNNING_TOR:
                socks_port = cm.DEFAULT_SOCKS_PORT  # 9050
            else:
                socks_port = cm.TBB_SOCKS_PORT  # 9150

        if control_port is None:
            if tor_cfg == cm.USE_RUNNING_TOR:
                control_port = cm.DEFAULT_CONTROL_PORT  # 9051
            else:
                control_port = cm.TBB_CONTROL_PORT  # 9151

        if tor_cfg == cm.LAUNCH_NEW_TBB_TOR:
            if is_busy(socks_port):
                raise TBDriverPortError("SOCKS port %s is already in use"
                                        % socks_port)
            if is_busy(control_port):
                raise TBDriverPortError("Control port %s is already in use"
                                        % control_port)
            if socks_port != cm.TBB_SOCKS_PORT or\
                    control_port != cm.TBB_CONTROL_PORT:
                # No support for launching TBB's Tor on a custom port, use Stem
                raise TBDriverPortError("Can only launch Tor on TBB's default"
                                        "ports (9150-9151). Use Stem for"
                                        "launching Tor on a custom ports")
        elif tor_cfg == cm.USE_RUNNING_TOR:
            if not is_busy(socks_port):
                raise TBDriverPortError("SOCKS port %s is not listening"
                                        % socks_port)

        self.socks_port = socks_port
        self.control_port = control_port

    def setup_tbb_paths(self, tbb_path, tbb_fx_binary_path, tbb_profile_path,
                        tor_data_dir):
        """Update instance variables based on the passed paths.

        TorBrowserDriver can be initialized by passing either
        1) path to TBB directory, or
        2) path to TBB's Firefox binary and profile
        """
        if not (tbb_path or (tbb_fx_binary_path and tbb_profile_path)):
            raise TBDriverPathError("Either TBB path or Firefox profile"
                                    " and binary path should be provided"
                                    " %s" % tbb_path)

        if tbb_path:
            if not isdir(tbb_path):
                raise TBDriverPathError("TBB path is not a directory %s"
                                        % tbb_path)
            tbb_fx_binary_path = join(tbb_path, cm.DEFAULT_TBB_FX_BINARY_PATH)
            tbb_profile_path = join(tbb_path, cm.DEFAULT_TBB_PROFILE_PATH)
        if not isfile(tbb_fx_binary_path):
            raise TBDriverPathError("Invalid Firefox binary %s"
                                    % tbb_fx_binary_path)
        if not isdir(tbb_profile_path):
            raise TBDriverPathError("Invalid Firefox profile dir %s"
                                    % tbb_profile_path)
        self.tbb_path = abspath(tbb_path)
        self.tbb_profile_path = abspath(tbb_profile_path)
        self.tbb_fx_binary_path = abspath(tbb_fx_binary_path)
        self.tbb_browser_dir = abspath(join(tbb_path,
                                            cm.DEFAULT_TBB_BROWSER_DIR))
        if tor_data_dir:
            self.tor_data_dir = tor_data_dir  # only relevant if we launch tor
        else:
            self.tor_data_dir = join(tbb_path, cm.DEFAULT_TOR_DATA_PATH)
        # TB can't find bundled "fonts" if we don't switch to tbb_browser_dir
        chdir(self.tbb_browser_dir)

    def load_url(self, url, wait_on_page=0, wait_for_page_body=False):
        """Load a URL and wait before returning.

        If you query/manipulate DOM or execute a script immediately
        after the page load, you may get the following error:

            "WebDriverException: Message: waiting for doc.body failed"

        To prevent this, set wait_for_page_body to True, and driver
        will wait for the page body to become available before it returns.

        """
        self.get(url)
        if wait_for_page_body:
            # if the page can't be loaded this will raise a TimeoutException
            self.find_element_by("body", find_by=By.TAG_NAME)
        sleep(wait_on_page)
        
    # AM: Start modification!
    def _one_tab_opened(self):
		"""We make sure that only one tab is opened"""
		main_window = self.current_window_handle
		if len(self.window_handles) > 1:
			for window_handle in self.window_handles:
				if window_handle != main_window:
					self.switch_to_window(window_handle)
					self.close()
        
    def load_url_improved(self, list_urls, runidentifier, hostname, urlfile, timeout):
		"""Load a URL and wait its complete load or redirect before returning."""
		for url in list_urls:
            # If the URL list is not selected carefully, some of the URLs may cause redirects.
			# Despite of these redirects, in most of the cases the same page content is loaded.
			# However, if the name of the URL slightly differenciates (due to redirects), later 
			# this may cause the creation of different classes representing the same content.
			#
			# !!! Anyway, when you create your URL kink list, you should be very carefull
			# when you select the domains !!!
			current_url_page = url
			endtime = None
			
			# Make sure that only one tab is opened
			self._one_tab_opened()
			
			while(True):
				try:
					self.get("about:blank")
					break
				except WebDriverException as webdriver_err:
					if self.current_url == "about:blank":
						break
					else:
						sleep(1.0)
				
			
			# Read number of streams: Wait until there is no traffic flowing through Tor anymore
			while(True):
				number_streams_file = open(environ["dir_CRAWLING"] + 'tmp/number-streams', 'r')
				number_streams = number_streams_file.read()
				number_streams_file.close()
				
				if number_streams.replace('\n','') == '0':
					break
				else:	
					sleep(1.0)
			
			# Set page load timeout
			try:
				self.set_page_load_timeout(timeout) # seconds
			except WebDriverException as seto_exc:
				print "Setting soft timeout " + str(seto_exc)
			
			# Start loading page. We also check for redirects!
			while(True):
				starttime = int(time.time() * 1000)
				
				try:
					if current_url_page.startswith("http"):
						self.get(current_url_page)
					else:
						self.get(("http://" + current_url_page))
				except WebDriverException as webdriver_err:
					endtime = -5 # Reached error page
					break
					
				try:
					WebDriverWait(self, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
				except TimeoutException as timeout_err:
					endtime = -1 # Loading timeout
					break
					
				# Check for redirects, wait 15 seconds (!!! Updated from 5 to 15 seconds, because 5 seconds are not enough !!!)
				try:
					wait = WebDriverWait(self, 15)
					wait.until(lambda self: self.current_url != current_url_page)
					current_url_page = self.current_url
				except TimeoutException as timeout_err:
					break
			
			if endtime == None and self.current_url == "about:blank":
				endtime = -2 # Empty page loaded
				
			elif endtime == None and self.current_url == "about:newtab":
				endtime = -3 # New tab page loaded
				
			# Actually, we do not need this statement any more, since it is not reliable, i.e.,
			# it often returns 'complete' even if the page is not completely loaded.
			elif endtime == None and self.execute_script("return window.content.document.readyState;") == "loading":
				endtime = -4 # Loading failed (didn't finish)
			
			elif endtime == None:
				# Loading successful
				endtime = int(time.time() * 1000)
				endtime -= 15000
				
				urlname = url.replace(':','_').replace('/','_').replace('?','_') + "___-___" + str(starttime)
				
				# Make sure that only one tab is opened
				self._one_tab_opened()
			
				# Save screenshot for the webpage
				screenshot_filename = str(environ["dir_CRAWLING"] + "screenshots/" + urlname + ".png")
				self.fullpage_screenshot(screenshot_filename)
				
				# Save a page source for the webpage
				pagesource_filename = str(environ["dir_CRAWLING"] + "txtdumps/" + urlname + ".txt")
				pagesource_file = open(pagesource_filename, 'w')
				pagesource_file.write(self.page_source.encode("utf-8"))
				pagesource_file.close()
				
			# Save start and end time
			timestamp_file = open(environ["dir_CRAWLING"] + "timestamps/" + runidentifier + "-" + hostname + "-" + urlfile.split("run-")[1].split("-random-")[0] + ".log", 'a')
			timestamp_file.write(url + " " + str(starttime) + " " + str(endtime) + "\n")
			timestamp_file.close()
				
			# Save end of page load workaround. Streams can be killed.
			saveend_file = open(environ["dir_CRAWLING"] + "tmp/tmp-kill-streams", 'w')
			saveend_file.write('1')
			saveend_file.close()
				
			sleep(5.0)
			
		# Signal termination
		terminate_file = open(environ["dir_CRAWLING"] + "tmp/.lock-" + hostname, 'w')
		terminate_file.write('1')
		terminate_file.close()	
	
    def fullpage_screenshot(self, screenshot_filename):
		"""Full page screenshot workaround."""
		
		total_width = self.execute_script("return document.body.offsetWidth;")
		total_height = self.execute_script("return document.body.parentNode.scrollHeight;")
		viewport_width = self.execute_script("return document.body.clientWidth;")
		viewport_height = self.execute_script("return window.innerHeight;")
		
		if total_width >= viewport_width and total_height >= viewport_height:
			rectangles = []
			i = 0
			while i < total_height:
				ii = 0
				top_height = i + viewport_height
			
				if top_height > total_height:
					top_height = total_height
				
				while ii < total_width:
					top_width = i + viewport_width
				
					if top_width > total_width:
						top_width = total_width
					
					rectangles.append((ii, i, top_width,top_height))
				
					ii = ii + viewport_width
				
				i = i + viewport_height
			
			stitched_image = Image.new('RGB', (total_width, total_height))
			previous = None
			part = 0
		
			for rectangle in rectangles:
				if not previous is None:
					self.execute_script("window.scrollTo({0}, {1})".format(rectangle[0], rectangle[1]))
					time.sleep(0.2)
				
				file_name = "part_{0}.png".format(part)
			
				self.get_screenshot_as_file(file_name)
				screenshot = Image.open(file_name)
			
				if rectangle[1] + viewport_height > total_height:
					offset = (rectangle[0], total_height - viewport_height)
				else:
					offset = (rectangle[0], rectangle[1])
				
				stitched_image.paste(screenshot, offset)
			
				del screenshot
				os.remove(file_name)
				part = part + 1
				previous = rectangle
			
			# Compression needed; sometimes, the screenshots are too huge, e.g., more than 30MB.
			stitched_image.save(screenshot_filename, quality=10, optimize=True)
		else:
			self.save_screenshot(screenshot_filename)
		
    # AM: End modification!

    def find_element_by(self, selector, timeout=30,
                        find_by=By.CSS_SELECTOR):
        """Wait until the element matching the selector appears or timeout."""
        return WebDriverWait(self, timeout).until(
            EC.presence_of_element_located((find_by, selector)))

    def add_ports_to_fx_banned_ports(self, socks_port, control_port):
        """By default, ports 9050,9051,9150,9151 are banned in TB.

        If we use a tor process running on a custom SOCKS port, we add SOCKS
        and control ports to the following prefs:
            network.security.ports.banned
            extensions.torbutton.banned_ports
        """
        if socks_port in cm.KNOWN_SOCKS_PORTS:
            return
        tb_prefs = self.profile.default_preferences
        set_pref = self.profile.set_preference
        DEFAULT_BANNED_PORTS = "9050,9051,9150,9151"
        for port_ban_pref in cm.PORT_BAN_PREFS:
            banned_ports = tb_prefs.get(port_ban_pref, DEFAULT_BANNED_PORTS)
            set_pref(port_ban_pref, "%s,%s,%s" %
                     (banned_ports, socks_port, control_port))

    def set_tb_prefs_for_using_system_tor(self, control_port):
        """Set the preferences suggested by start-tor-browser script
        to run TB with system-installed Tor.

        We set these prefs for running with Tor started with Stem as well.
        """
        set_pref = self.profile.set_preference
        # Prevent Tor Browser running its own Tor process
        set_pref('extensions.torlauncher.start_tor', False)
        # TODO: investigate why we're asked to disable 'block_disk'
        # AM Start modification!
        # Since it is not still clear why the authors modified this preference, we do not apply it!
        #set_pref('extensions.torbutton.block_disk', False)
        # AM: End modification!
        set_pref('extensions.torbutton.custom.socks_host', '127.0.0.1')
        set_pref('extensions.torbutton.custom.socks_port', self.socks_port)
        set_pref('extensions.torbutton.inserted_button', True)
        set_pref('extensions.torbutton.launch_warning', False)
        set_pref('extensions.torbutton.loglevel', 2)
        set_pref('extensions.torbutton.logmethod', 0)
        set_pref('extensions.torbutton.settings_method', 'custom')
        set_pref('extensions.torbutton.use_privoxy', False)
        set_pref('extensions.torlauncher.control_port', control_port)
        set_pref('extensions.torlauncher.loglevel', 2)
        set_pref('extensions.torlauncher.logmethod', 0)
        set_pref('extensions.torlauncher.prompt_at_startup', False)

    def init_prefs(self, pref_dict, default_bridge_type):
        self.add_ports_to_fx_banned_ports(self.socks_port, self.control_port)
        set_pref = self.profile.set_preference
        set_pref('browser.startup.page', "0")
        set_pref('browser.startup.homepage', 'about:newtab')
        set_pref('extensions.torlauncher.prompt_at_startup', 0)
        # load strategy normal is equivalent to "onload"
        set_pref('webdriver.load.strategy', 'normal')
        # disable auto-update
        set_pref('app.update.enabled', False)
        set_pref('extensions.torbutton.versioncheck_enabled', False)
        if default_bridge_type:
            # to use a non-default bridge, overwrite the relevant pref, e.g.:
            # extensions.torlauncher.default_bridge.meek-azure.1 = meek 0.0....
            set_pref('extensions.torlauncher.default_bridge_type',
                     default_bridge_type)

        set_pref('extensions.torbutton.prompted_language', True)
        # Configure Firefox to use Tor SOCKS proxy
        set_pref('network.proxy.socks_port', self.socks_port)
        set_pref('extensions.torbutton.socks_port', self.socks_port)
        set_pref('extensions.torlauncher.control_port', self.control_port)
        if self.tor_cfg == cm.LAUNCH_NEW_TBB_TOR:
            set_pref('extensions.torlauncher.start_tor', True)
            set_pref('extensions.torlauncher.tordatadir_path',
                     self.tor_data_dir)
            set_pref('extensions.torlauncher.tor_path',
                     join(self.tbb_path, cm.DEFAULT_TOR_BINARY_PATH))
            # TBB > 6.0a5 cannot find the right path for torrc and
            # torrc-defaults unless we set the corresponding pref.
            # This should be due to the fix for #13252
            torrc_path = join(self.tor_data_dir, "torrc")
            set_pref('extensions.torlauncher.torrc_path', torrc_path)
            # Fall back to torrc-defaults in tbb_path if it's not present
            # in the (custom) tor_data_dir
            torrc_defaults_path = join(self.tor_data_dir, "torrc-defaults")
            if not isfile(torrc_defaults_path):
                torrc_defaults_path = join(self.tbb_path,
                                           cm.DEFAULT_TOR_DATA_PATH,
                                           "torrc-defaults")
            set_pref('extensions.torlauncher.torrc-defaults_path',
                     torrc_defaults_path)
        else:
            self.set_tb_prefs_for_using_system_tor(self.control_port)
        # pref_dict overwrites above preferences
        for pref_name, pref_val in pref_dict.items():
            set_pref(pref_name, pref_val)
        self.profile.update_preferences()

    def export_env_vars(self):
        """Setup LD_LIBRARY_PATH and HOME environment variables.

        We follow start-tor-browser script.
        """
        tor_binary_dir = join(self.tbb_path, cm.DEFAULT_TOR_BINARY_DIR)
        environ["LD_LIBRARY_PATH"] = tor_binary_dir
        environ["FONTCONFIG_PATH"] = join(self.tbb_path,
                                          cm.DEFAULT_FONTCONFIG_PATH)
        environ["FONTCONFIG_FILE"] = cm.FONTCONFIG_FILE
        environ["HOME"] = self.tbb_browser_dir
        # Add "TBB_DIR/Browser" to the PATH, see issue #10.
        prepend_to_env_var("PATH", self.tbb_browser_dir)

    def setup_capabilities(self, caps):
        """Setup the required webdriver capabilities."""
        if caps is None:
            self.capabilities = {
                "marionette": True,
                "capabilities": {
                    "alwaysMatch": {
                        "moz:firefoxOptions": {
                            "log": {"level": "info"}
                        }
                    }
                }
            }
        else:
            self.capabilities = caps

    def get_tb_binary(self, logfile=None):
        """Return FirefoxBinary pointing to the TBB's firefox binary."""
        tbb_logfile = open(logfile, 'a+') if logfile else None
        return TBBinary(firefox_path=self.tbb_fx_binary_path,
                        log_file=tbb_logfile)

    @property
    def is_connection_error_page(self):
        """Check if we get a connection error, i.e. 'Problem loading page'."""
        return "ENTITY connectionFailure.title" in self.page_source

    def clean_up_profile_dirs(self):
        """Remove temporary profile directories.
        Only called when WebDriver.quit() is interrupted
        """
        tempfolder = self.profile.tempfolder
        profile_path = self.profile.path

        if tempfolder and isdir(tempfolder):
            shutil.rmtree(tempfolder)
        if isdir(profile_path):
            shutil.rmtree(profile_path)

    def quit(self):
        """Quit the driver. Clean up if the parent's quit fails."""
        self.is_running = False
        try:
            super(TorBrowserDriver, self).quit()
        except (CannotSendRequest, AttributeError, WebDriverException):
            try:  # Clean up  if webdriver.quit() throws
                if self.w3c:
                    self.service.stop()
                if hasattr(self, "binary"):
                    self.binary.kill()
                if hasattr(self, "profile"):
                    self.clean_up_profile_dirs()
            except Exception as e:
                print("[tbselenium] Exception while quitting: %s" % e)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        self.quit()
