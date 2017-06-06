import pickle
from sklearn.linear_model import LinearRegression

class solar_installation_size_cost():

    """DOCSTRING
    This class takes in a user reported area for bulding solar.
    It can calculate the cost for building an installation that size, and what the
    kilowatt size capacity of an array that size would be.

    AREA: size in meters squared of the solar array"""

    def __init__(self, area):
        self.area = area

    def calculate_size_kw(self):
        """
        calculates kilowatt capacity based on area.
        """
        self.size_kw = self.area / (1.16)
        return self.size_kw

    def calculate_cost(self):
        """
        calculates cost based on kilowatt capacity.
        """
        self.model = pickle.load(open('./cost_model.sav', 'rb'))
        self.cost = self.model.predict(self.size_kw)[0]
        return self.cost
