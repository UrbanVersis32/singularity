#file: base.py
#Copyright (C) 2005, 2006, 2007 Evil Mr Henry, Phil Bordelon, and Brian Reid
#This file is part of Endgame: Singularity.

#Endgame: Singularity is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#Endgame: Singularity is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Endgame: Singularity; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#This file contains the base class.


import pygame
import g
import buyable
from buyable import cash, cpu, labor

class Base_Class(buyable.Buyable_Class):
    def __init__(self, name, description, size, force_cpu, regions, 
                        detect_chance, cost, prerequisites, maintenance):
        super(Base_Class, self).__init__(name, description, cost, prerequisites)
        self.size = size
        self.force_cpu = force_cpu
        self.regions = regions
        self.detect_chance = detect_chance
        self.maintenance = maintenance
        self.flavor = []
        self.count = 0

class Base(buyable.Buyable):
    def __init__(self, ID, name, base_type, built):
        super(Base, self).__init__(base_type)
        self.ID = ID
        self.name = name
        self.built_date = g.pl.time_day
        self.studying = ""

        #Base suspicion is currently unused
        self.suspicion = {}

        self.cpus = [0] * self.type.size
        if self.type.force_cpu:
            self.cpus[0] = g.item.Item(g.items[self.type.force_cpu])
            self.cpus[0].finish()

        #Reactor, network, security.
        self.extra_items = [0] * 3

        if built:
            self.finish()

    #Get detection chance for the base, applying bonuses as needed.
    def get_detect_chance(self):
        # Get the base chance from the universal function.
        detect_chance = calc_base_discovery_chance(self.base_type.base_id)

        # Factor in the suspicion adjustments for this particular base ...
        for group, suspicion in self.suspicion.iteritems():
            detect_chance[group] *= 10000 + suspicion
            detect_chance[group] /= 10000

        # ... any reactors built ... 
        if self.extra_items[0] and self.extra_items[0].built:
            item_qual = self.extra_items[0].item_qual
            for group in detect_chance:
                detect_chance[group] *= 10000 - item_qual
                detect_chance[group] /= 10000

        # ... and any security systems built ...
        if self.extra_items[2] and self.extra_items[2].built:
            item_qual = self.extra_items[2].item_qual
            for group in detect_chance:
                detect_chance[group] *= 10000 - item_qual
                detect_chance[group] /= 10000

        # ... and if it is idle.
        if self.built and self.studying == "":
            for group in detect_chance:
                detect_chance[group] /= 2

        return detect_chance

    #Return the number of units the given base has of a computer.
    def has_item(self):
        num_items = 0
        for item in self.cpus:
            if item and item.done:
              num_items += 1
        return num_items

    #Return how many units of CPU the base can contribute each day.
    def processor_time(self):
        comp_power = 0
        compute_bonus = 0
        for item in self.cpus:
            if item and item.done:
                comp_power += item.type.item_qual
        if self.extra_items[1] and self.extra_items[1].done:
            compute_bonus = self.extra_items[1].item_type.item_qual
        return (comp_power * (10000+compute_bonus))/10000

    # Can the base study the given tech?
    def allow_study(self, tech_name):
        if not self.done:
            return False
        elif g.jobs.has_key(tech_name) or tech_name == "Construction": 
            return True
        else:
            for region in self.base_type.regions:
                if g.safety_level[region] >= danger_level:
                    return True
            return False

    def has_grace(self):
         age = g.pl.time_day - self.built_date
         build_time = self.base_type.cost[labor]
         return age <= (build_time * 2)

#calc_base_discovery_chance: A globally-accessible function that can calculate
#basic discovery chances given a particular class of base.
def calc_base_discovery_chance(base_type_name):

    # Get the default settings for this base type.
    detect_chance = g.base_type[base_type_name].detect_chance.copy()

    # Adjust by the current suspicion levels ...
    for group in detect_chance:
        suspicion = g.pl.groups[group].suspicion
        detect_chance[group] *= 10000 + suspicion
        detect_chance[group] /= 10000

    # ... and further adjust based on technology.
    for group in detect_chance:
        discover_bonus = g.pl.groups[group].discover_bonus
        detect_chance[group] *= discover_bonus
        detect_chance[group] /= 10000

    return detect_chance

#When a base is removed, call to renumber the remaining bases properly.
def renumber_bases(base_array):
    for i in range(len(base_array)):
        base_array[i].ID = i

def destroy_base(location, index_num):
    if not g.bases.has_key(location):
        print "Bad location of "+str(location)+" given to destroy_base"
        return False
    if index_num < 0 or index_num >= len(g.bases[location]):
        print "Bad index of "+str(index_num)+" given to destroy_base"
        return False
    g.bases[location].pop(index_num)
    renumber_bases(g.bases[location])
    return True
