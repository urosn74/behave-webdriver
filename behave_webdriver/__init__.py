import time
from functools import partial
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.color import Color
from selenium.webdriver.support.select import Select as _Select

from .conditions import (element_is_present,
                         element_is_selected,
                         element_contains_value,
                         element_is_visible,
                         element_contains_text,
                         element_is_enabled)


class Select(_Select):
    def select_by_attr(self, attr, attr_value):
        css = 'option[{} ={}]'.format(attr, self._escapeString(attr_value))
        opts = self._el.find_elements(By.CSS_SELECTOR, css)
        matched = False
        for opt in opts:
            self._setSelected(opt)
            matched = True
            if not self.is_multiple:
                return
        if not matched:
            raise NoSuchElementException("Cannot locate option by {} attribue with value of '{}'".format(attr,
                                                                                                         attr_value))


class BehaveDriver(object):
    """
    Implements most of the logic for step definitions.
    Instances of this class are fully substitutable with selenium webdriver.
    The behave driver can be used just like you would any other selenium webdriver.

    >>> behave_driver = BehaveDriver.chrome()
    >>> behave_driver.get('https://google.com/')

    If, for some reason, you need it, you can access the actual driver instance by the ``.driver`` attribute.
    """

    def __init__(self, driver, default_wait=None):
        """

        :param driver: a selenium webdriver instance
        :param default_wait: number of seconds to wait for elements (for expected conditions) by default.
        """
        self.driver = driver
        self.default_wait = default_wait

    def __getattr__(self, item):
        if hasattr(self.driver, item):
            return getattr(self.driver, item)
        else:
            raise AttributeError('{} has no attribute {}'.format(self, item))

    @classmethod
    def chrome(cls, *args, **kwargs):
        """
        Alternative constructor. Creates BehaveDriver instance using standard chromedriver.

        :param args: positional args passed to `webdriver.Chrome`
        :param kwargs: keyword args passed to `webdriver.Chrome`
        :return: a BehaveDriver instance
        """
        driver = webdriver.Chrome(*args, **kwargs)
        return cls(driver=driver)

    @classmethod
    def firefox(cls, *args, **kwargs):
        """
        Alternative constructor. Creates a BehaveDriver instance using standard firefox gecko driver.

        :param args: dirver args
        :param kwargs: driver kwargs
        :return: a BehaveDriver instance
        """
        driver = webdriver.Firefox(*args, **kwargs)
        return cls(driver=driver)

    @classmethod
    def phantom_js(cls, *args, **kwargs):
        """
        Alternative constructor. Creates a BehaveDriver instance using standard phantomJS driver.

        :param args: dirver args
        :param kwargs: driver kwargs
        :return: a BehaveDriver instance
        """
        driver = webdriver.PhantomJS(*args, **kwargs)
        return cls(driver=driver)

    @classmethod
    def safari(cls, *args, **kwargs):
        """
        Alternative constructor. Creates a BehaveDriver instance using standard safari driver.

        :param args: dirver args
        :param kwargs: driver kwargs
        :return: a BehaveDriver instance
        """
        driver = webdriver.Safari(*args, **kwargs)
        return cls(driver=driver)

    @classmethod
    def headless_chrome(cls, *args, **kwargs):
        """
        Alternate constructor. Creates a BehaveDriver instance using a chromrdriver with headless options
        (``--headless`` and ``--disable-gpu``)

        :param args: positional args passed to `webdriver.Chrome`
        :param kwargs: keyword args passed to `webdriver.Chrome`
        :return: a BehaveDriver instance
        """
        chrome_options = kwargs.pop('chrome_options', None)
        if chrome_options is None:
            chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(*args, chrome_options=chrome_options, **kwargs)
        return cls(driver=driver)

    @property
    def alert(self):
        """
        Property shortcut for an ``Alert`` object for the driver
        Note: this will return an Alert instance regardless of whether or not there is actually an alert present.
        Use ``has_alert`` to check whether or not there is an alert currently present.

        :return: an selenium.webdriver.common.alert.Alert instance
        """
        return self.driver.switch_to.alert

    @property
    def screen_size(self):
        """
        Property for the current screen size. Can also be set by assigning an x/y tuple.

        :return: tuple of the screen dimensions (x, y)
        """
        size = self.driver.get_window_size()
        x = size['width']
        y = size['height']
        return (x, y)

    @screen_size.setter
    def screen_size(self, size):
        """
        :param size: The dimensions to set the screen to in (x, y) format.
        :type size: tuple
        :return:
        """
        x, y = size
        if x is None:
            x = self.screen_size[0]
        if y is None:
            y = self.screen_size[1]
        self.driver.set_window_size(x, y)

    @property
    def cookies(self):
        """
        Shortcut for driver.get_cookies()
        """
        return self.driver.get_cookies()

    @property
    def has_alert(self):
        """
        Whether or not there is currently an alert present

        :return: True if there is an alert present, else False
        :rtype: bool
        """
        try:
            WebDriverWait(self.driver, 1).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            return True
        except TimeoutException:
            return False

    def get_cookie(self, cookie_name):
        """
        retrieve a cookie with a particular name

        :param cookie_name: the name of the cookie
        :type cookie_name: str
        :return: A dictionary containing the cookie information
        :rtype: dict
        """
        return self.driver.get_cookie(cookie_name)

    def get_element(self, selector, by=None):
        """
        Takes a selector string and uses an appropriate method (XPATH or CSS selector by default) to find a WebElement
        The optional `by` argument can be supplied to specify any locating method explicitly.
        This is used to resolve selectors from step definition strings to actual element objects

        :param selector: The selector to use, an XPATH or CSS selector
        :type selector: str
        :param by: alternate method used to locate element, e.g. (By.id) See selenium.webdriver.common.by.By attributes
        :return: WebElement object
        """
        if by:
            return self.driver.find_element(by, selector)
        if selector.startswith('//'):
            return self.driver.find_element_by_xpath(selector)
        else:
            return self.driver.find_element_by_css_selector(selector)

    def get_element_text(self, element):
        """
        Takes in a selector, finds the element, and extracts the text.
        When present on the WebElement, the element's 'value' property is returned. (For example, this is useful for
        getting the current text of Input elements)
        If the element has no 'value' property, the containing text is returned (elem.text)

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :return: the text contained within the element.
        :rtype: str
        """
        elem = self.get_element(element)
        value = elem.get_property('value')
        if value is not None:
            return value
        return elem.text

    def get_element_attribute(self, element, attr, css=False, expected_value=None):
        """
        Get the value of an attribute or css attribute from an element.

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :param attr: The attribute to lookup
        :type attr: str
        :param css: Whether or not this is a CSS atrribute
        :type css: bool
        :param expected_value:
        :return: The value of the attribute
        """
        elem = self.get_element(element)
        if css:
            value = elem.value_of_css_property(attr)
            if self.is_color(value):
                value = Color.from_string(value)
            if expected_value:
                if self.is_color(expected_value):
                    expected_value = Color.from_string(expected_value)
                return value, expected_value
        else:
            value = elem.get_attribute(attr)
        return value

    def get_element_size(self, element):
        """
        Returns a dictionary containing the size information of an element.
        The dictionary has two keys: 'width' and 'height' which represent the size of the element dimensions in px

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :return: A dictionary with size information
        :rtype: dict
        """
        elem = self.get_element(element)
        return elem.size

    def get_element_location(self, element):
        """
        Gets the location of the element in the renderable canvas.
        This is a dict with two keys: 'x' and 'y'

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :return: the element's location
        :rtype: dict
        """
        elem = self.get_element(element)
        return elem.location

    def open_url(self, url):
        """
        Navigate to an absolute URL
        Behaves same as ``driver.get`` but serves as a common entry-point for subclasses wanting to change this.

        :param url: an absolute URL including the scheme
        :type url: str
        :return:
        """
        return self.driver.get(url)

    def element_exists(self, element):
        """
        Whether or not an element exists. Attempts to locate the element using `get_element` returns True if the element
        was found, False if it couldn't be located.

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :return: True if the element could be found, False if it couldn't be found
        :rtype: bool
        """
        try:
            self.get_element(element)  # attempt to get the element
            return True  # if it succeeded, return True
        except NoSuchElementException:
            # The element was not able to be located
            return False

    def element_visible(self, element):
        """
        Checks if an element is visible or not.

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :return: True if the element is visible, else False
        :rtype: bool
        """
        elem = self.get_element(element)
        return elem.is_displayed()

    def element_in_viewport(self, element):
        """
        Determines the bounding box (rect) of the window and rect of the element.
        This information is used to determine whether or not the element is *completely* within the viewport.

        :param element: CSS Selector or XPATH used to locate the element
        :return:
        """
        elem = self.get_element(element)
        elem_left_bound = elem.location.get('x')
        elem_top_bound = elem.location.get('y')
        elem_width = elem.size.get('width')
        elem_height = elem.size.get('height')
        elem_right_bound = elem_left_bound + elem_width
        elem_lower_bound = elem_top_bound + elem_height

        win_upper_bound = self.driver.execute_script('return window.pageYOffset')
        win_left_bound = self.driver.execute_script('return window.pageXOffset')
        win_width = self.driver.execute_script('return document.documentElement.clientWidth')
        win_height = self.driver.execute_script('return document.documentElement.clientHeight')
        win_right_bound = win_left_bound + win_width
        win_lower_bound = win_upper_bound + win_height

        return all((win_left_bound <= elem_left_bound,
                    win_right_bound >= elem_right_bound,
                    win_upper_bound <= elem_top_bound,
                    win_lower_bound >= elem_lower_bound)
                   )

    def element_enabled(self, element):
        """
        Checks if an element is enabled or not.

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :return: True if the element is enabled, else False
        :rtype: bool
        """
        elem = self.get_element(element)
        return elem.is_enabled()

    def element_focused(self, element):
        elem = self.get_element(element)
        focused_elem = self.driver.switch_to.active_element
        return elem == focused_elem

    def element_selected(self, element):
        """
        Checks if an element is selected or not.

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :return: True if the element is selected, else False
        :rtype: bool
        """
        elem = self.get_element(element)
        return elem.is_selected()

    def element_contains(self, element, value):
        """
        Checks if an element contains (in value/text) a given string/value

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :param value: the text/value to check for
        :type value: str
        :return: True or False, whether or not the value was found in the element.
        :rtype: bool
        """
        elem = self.get_element(element)
        element_value = elem.get_property('value')
        if element_value is None:
            element_value = elem.text
        return value in element_value

    def element_has_class(self, element, cls):
        """
        Checks whether or not an element has a particular css class.

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :param cls: The css class to check for
        :type cls: str
        :return: True if the element has the specified class, else False
        :rtype: bool
        """
        elem = self.get_element(element)
        elem_classes = elem.get_attribute('class')
        return cls in elem_classes

    def click_element(self, element):
        """
        Click on an element. Note: this will not trigger some doubleclick events, even when n=2 with any delay.
        Instead, if you want to doubleclick, use `doubleclick_element`

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        """
        elem = self.get_element(element)
        elem.click()

    def doubleclick_element(self, element):
        """
        Double click an element

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :return:
        """
        elem = self.get_element(element)
        actions = ActionChains(self.driver)
        actions.double_click(elem)
        actions.perform()

    def click_link_text(self, text, partial=False):
        """
        Click on a link, located by matching the text contained in the link. If ``partial`` is True,
        the link is located by partial text.

        :param text: The text contained in the link, used to locate the element.
        :type text: str
        :param partial: Whether or not to match link by partial text (as opposed to full match)
        :type partial: bool
        :return:
        """
        if partial:
            self.driver.find_element_by_partial_link_text(text).click()
        else:
            self.driver.find_element_by_link_text(text).click()

    def drag_element(self, element, to_element):
        """
        Drag an element to the location of another element.

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :param to_element: the selector used to locate the destination element
        :type to_element: str
        :return:
        """
        source_elem = self.get_element(element)
        to_elem = self.get_element(to_element)
        actions = ActionChains(self.driver)
        actions.drag_and_drop(source_elem, to_elem)
        actions.perform()

    def submit(self, element):
        """
        Shortcut for submitting an element

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :return:
        """
        elem = self.get_element(element)
        elem.submit()

    def send_keys(self, keys):
        """
        Send arbitrary keys. Note: this is different than sending keys directly to an element.

        :param keys: keys to send
        :return:
        """
        actions = ActionChains(self.driver)
        actions.send_keys(keys)
        actions.perform()

    def press_button(self, button):
        """
        Send a keystroke simulating the press of a given button. You can use keys as strings (e.g. 'a', 'z') or any
        key names (e.g. the 'escape' key). When the length of the button argument is greater than one character,
        names are checked against selenium.webdriver.common.keys.Keys first.

        :param button: A single character or key name
        :type button: str
        :return:
        """
        if len(button) > 1:
            button = getattr(Keys, button.upper(), button)
        self.send_keys(button)

    def scroll_to_bottom(self):
        """
        Scrolls the current window to the bottom of the window (0, document.body.scrollHeight).
        """
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def scroll_to_element(self, element):
        """
        Scroll to the location of an element.

        :param element: CSS Selector or XPATH used to locate the element
        :return:
        """
        location = self.get_element_location(element)
        x = location['x']
        y = location['y']
        self.scroll_to(x, y)

    def scroll_to(self, x, y):
        """
        Scroll to a particular (x, y) coordinate.

        :param x: the x coordinate to scroll to.
        :type x: int
        :param y: the y coordinate to scroll to.
        :type y: int
        :return:
        """
        # prevent script injection
        x = int(x)
        y = int(y)
        self.driver.execute_script('window.scrollTo({}, {});'.format(x, y))

    def move_to_element(self, element, offset=None):
        """
        Moves the mouse to the middle of an element

        :param element: CSS Selector or XPATH used to locate the element
        :type element: str
        :param offset: optional tuple of x/y offsets to offset mouse from center
        :type offset: tuple
        :return:
        """
        elem = self.get_element(element)
        actions = ActionChains(self.driver)
        if offset:
            actions.move_to_element_with_offset(elem, *offset)
        else:
            actions.move_to_element(elem)
        actions.perform()

    def pause(self, milliseconds):
        """
        Pause for a number of miliseconds.
        ``time.sleep`` is used here due to issues with w3c browsers and ActionChain pause feature.

        :param milliseconds: number of miliseconds to wait
        :type milliseconds: int
        :return:
        """
        seconds = round(milliseconds / 1000, 3)
        time.sleep(seconds)

    def wait_for_element_condition(self, element, ms, negative, condition):
        """
        Wait on an element until a certain condition is met, up to a maximum amount of time to wait.

        :param element: CSS Selector or XPATH used to locate the element
        :param ms: maximum time (in milliseconds) to wait for the condition to be true
        :param negative: whether or not the check for negation of condition. Will coarse boolean from value
        :param condition: the condition to check for. Defaults to checking for presence of element
        :return: element
        """
        if not ms:
            seconds = self.default_wait or 1.5
        else:
            seconds = round(ms / 1000, 3)

        condition_text_map = {
            'be checked': element_is_selected,
            'be enabled': element_is_enabled,
            'be selected': element_is_selected,
            'be visible': element_is_visible,
            'contain a text': element_contains_text,
            'contain a value': element_contains_value,
            'exist': element_is_present,
        }

        if condition:
            expected = condition_text_map[condition]
        else:
            expected = element_is_present

        if element.startswith('//'):
            locator = (By.XPATH, element)
        else:
            locator = (By.CSS_SELECTOR, element)

        wait = WebDriverWait(self.driver, seconds)

        try:
            result = wait.until(expected(locator, negative=bool(negative)))
        except TimeoutException:
            result = None

        return result

    def select_option(self, select_element, by, by_arg):
        """
        Implements features for selecting options in Select elements. Uses selenium's ``Select`` support class.

        :param select_element: CSS Selector or XPATH used to locate the select element containing options
        :param by: the method for selecting the option, valid options include any select_by_X supported by ``Select``.
        :type by: str
        :return:
        """

        select_elem = self.get_element(select_element)
        select = Select(select_elem)
        select_method = getattr(select, 'select_by_'+by, partial(select.select_by_attr, by))
        select_method(by_arg)

    @staticmethod
    def is_color(str_):
        """
        Whether or not the string represents a color.

        :param str_:
        :return:
        """
        try:
            Color.from_string(str_)
            return True
        except ValueError:
            return False
