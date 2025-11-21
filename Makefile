#MAKEFILE

SRC_DIR := ./src/
################################################################################

SRCS       := $(wildcard $(SRC_DIR)*.cpp)
OBJS       := $(patsubst $(SRC_DIR)%.cpp, $(OBJ_DIR)%.o, $(SRCS))
################################################################################

TARGET      = #Your filename

CXX         = g++
CXXFLAGS    = -O3 -Wall -g -std=c++11
LIB         = 
INCLUDE     = 

#################################################################################

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) $(OBJS) $(LIB) -o $(TARGET)

./obj/%.o: ./src/%.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDE) -c $< -o $@

clean:
	rm -f $(TARGET) ./obj/*.o core *~
