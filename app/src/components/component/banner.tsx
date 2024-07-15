export const BannerComponent = () => {
  return (
    <div className="container flex flex-col items-center justify-between p-4 md:flex-row md:justify-around">
      <img
        src="https://scontent.fdvo5-1.fna.fbcdn.net/v/t39.30808-6/296872854_152331230736899_7630776868433262212_n.jpg?_nc_cat=109&ccb=1-7&_nc_sid=5f2048&_nc_eui2=AeE8kQuvuSzZq6w0nIN0y8zFhz1ymobZ69-HPXKahtnr3_M0id6Th3PL4Tgu6o6YHF5EhreTqrkZf7UR_h8N7aKi&_nc_ohc=C1fZlOj_bewQ7kNvgH6l9PM&_nc_ht=scontent.fdvo5-1.fna&oh=00_AYCa7dRts-MXcHQr1cOayZ9rpGr-2pg9lvr4VZu5hcy7eQ&oe=666763AE"
        className="object-cover w-32 h-32 mb-4 rounded-full md:w-48 md:h-48 md:mb-0"
      />
      <div className="flex flex-col items-center justify-center gap-2 text-center">
        <h1 className="text-3xl font-bold text-green-700 uppercase md:text-5xl">
          Auto-Waste Segregation
        </h1>
        <p className="text-md text-primary/95">
          Efficient separation of waste into categories for effective recycling
          and disposal.
        </p>
      </div>
      <img
        src="https://upload.wikimedia.org/wikipedia/en/c/c0/JH_Cerilles_State_College_logo.jpg"
        className="w-32 mt-4 h-36 md:w-48 md:h-52 md:mt-0"
      />
    </div>
  );
};
