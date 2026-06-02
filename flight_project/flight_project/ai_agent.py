def get_ai_response(user_message):

    user_message = user_message.lower()

    indian_cities = [

        "hyderabad",
        "delhi",
        "mumbai",
        "chennai",
        "bangalore",
        "kolkata",
        "pune",
        "ahmedabad",
        "goa",
        "kochi",
        "vizag",
        "tirupati",
        "jaipur",
        "lucknow",
        "bhopal",
        "patna",
        "nagpur",
        "indore",
        "surat",
        "vijayawada"
    ]

    found_cities = []

    for city in indian_cities:

        if city in user_message:

            found_cities.append(city.title())

    # FLIGHT SEARCH
    if len(found_cities) >= 2:

        from_city = found_cities[0]
        to_city = found_cities[1]

        return f"""
        Flights Available
        
        Route:
        {from_city} → {to_city}
        
        Airlines:
        • Indigo
        • Air India
        • Vistara
        • SpiceJet
        
        Timings:
        • 6:00 AM
        • 10:30 AM
        • 6:45 PM
        
        Ticket Price:
        ₹4500 - ₹9000
        
        Status:
        Seats Available
        """

    # PRICE
    elif "price" in user_message:

        return """
        Flight ticket prices in India usually range from:
        
        ₹3500 to ₹12000
        
        depending on city and timing.
        """

    # TICKET
    elif "ticket" in user_message:

        return """
        Flight ticket booking is available.
        
        You can search routes and reserve seats.
        """

    # FLIGHTS
    elif "flight" in user_message:

        return """
        Domestic flights available across India.
        
        Popular Routes:
        
        • Hyderabad → Delhi
        • Chennai → Mumbai
        • Bangalore → Kolkata
        • Pune → Goa
        • Vizag → Tirupati
        """

    # HELP
    else:

        return """
        Ask questions like:
        
        • Flights from Hyderabad to Delhi
        • Chennai to Mumbai flights
        • Ticket price
        • Available flights in India
        """